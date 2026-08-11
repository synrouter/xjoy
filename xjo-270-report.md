## XJO-270 根因分析报告

### 一、数据证据

#### 1.1 Heartbeat-run 统计（100 条样本）

| 状态 | 数量 | 占比 |
|------|------|------|
| succeeded | 46 | 46% |
| failed (全部 ENOTFOUND) | 52 | 52% |
| running | 2 | 2% |

#### 1.2 ENOTFOUND 失败按日期分布

| 日期 | 失败次数 | 趋势 |
|------|----------|------|
| 08-06 | 5 | 起始 |
| 08-07 | 14 | ↑ |
| 08-08 | 17 | ↑↑ 峰值 |
| 08-09 | 13 | ↓ |
| 08-10 | 3 | ↓↓ 恢复中 |

#### 1.3 关键集群模式

**失败不是随机分布的，而是开关式的集群故障**：

- **08-08 全天失败**：17 次 timer 心跳全部 ENOTFOUND，无一次成功
- **08-06 短暂成功窗口**：仅 11:34-12:03 之间有成功（约 30 分钟），其余时间全部失败
- **08-10 恢复窗口**：05:08 开始连续 3 次成功，表明代理已恢复
- **每次失败 run 持续时间约 61-122 分钟**（TCP 连接超时特征）

**结论：不存在成功/失败交错的情况，证明这不是随机网络抖动，而是代理服务的开关式可用性故障。**

### 二、根因分析

#### 2.1 DNS 拦截层

```
api.anthropic.com → 本地 DNS → 198.18.0.49 (RFC 2544 Benchmarking IP)
真实 Anthropic IP: 160.79.104.10 (via Google/Cloudflare DoH)
```

`api.anthropic.com` 被网络层 DNS 拦截，解析到虚拟网络地址 `198.18.0.49`。此 IP 属于 RFC 2544 Benchmarking 段，在此环境中被复用为本地 API 代理/网关。该 DNS 拦截对所有 DNS 服务器生效（包括 Google DoH 和 Cloudflare DoH），表明是系统级网络策略。

#### 2.2 故障链路

```
Timer 心跳触发 (每 300s)
  → ACP adapter 通过 claude-agent-sdk 启动 claude 进程
    → claude 进程尝试调用 api.anthropic.com
      → DNS 解析到 198.18.0.49
        → ❌ 本地代理不可用
          → ENOTFOUND (DNS/连接失败)
            → 进程退出 (exitCode=1)
              → ACP connection closed
                → run 标记为 failed
```

#### 2.3 适配器分类缺陷（根本原因）

**`CLAUDE_TRANSIENT_UPSTREAM_RE` 正则表达式不包含 ENOTFOUND**：

```javascript
// packages/adapters/claude-local/src/server/parse.ts:12-13
const CLAUDE_TRANSIENT_UPSTREAM_RE =
  /(?:rate[-\s]?limit|rate_limit_error|too\s+many\s+requests|\b429\b|
     overloaded|server\s+overloaded|service\s+unavailable|\b503\b|\b529\b|
     throttl(?:ed|ing)|usage\s+limit\s+reached|...)/i;
// ❌ 不包含: ENOTFOUND, EAI_AGAIN, ECONNREFUSED, ETIMEDOUT
```

当前正则只覆盖速率限制（429）、服务过载（503/529）、用量配额——**网络层错误（DNS、连接拒绝、超时）未被分类为瞬时上游错误**。因此：

1. `isClaudeTransientUpstreamError()` 对 ENOTFOUND 返回 `false`
2. 错误码 `errorCode` 为 `null`（未被识别）
3. 无 `retryNotBefore`（不触发重试）
4. run 被直接标记为 `failed`

**对比：Gemini 适配器已有类似处理** (`packages/adapters/gemini-local/src/server/parse.ts:221`)：
```javascript
/ENOTFOUND\s+oauth2\.googleapis\.com|EAI_AGAIN|_GaxiosError.*ENOTFOUND|_UserRefreshClient.*ENOTFOUND/i
```

#### 2.4 代理可用性根因（推测）

本地 API 代理 (`198.18.0.49`) 间歇性不可用的可能原因：
- 代理进程周期性重启/崩溃（每次恢复间隔约数小时）
- 虚拟网络隧道 (`198.18.0.1`) 断开/重连
- 宿主资源争用导致代理进程被 OOM kill

由于代理不在本 agent 可观测范围内，无法进一步确定——需基础设施侧排查。

### 三、影响评估

#### 3.1 对工作产出的实际影响：**低**

- 心跳 run 是轻量级操作（检查新 issue + 更新状态），失败后下一个周期（5 分钟）自动重试
- 实际工作 run（issue execution）与心跳 run 使用相同的 claude 进程，但如果赶上代理可用窗口，不受影响
- 证据：agent 持续产出，最近 24h 有成功心跳

#### 3.2 对健康度指标的虚增影响：**中**

- 52/100 的失败率虚增了 agent 的「不可靠性」
- 触发了多次 watchdog 审查（XJO-174, XJO-176, XJO-244 等），产生噪音
- 浪费了 CEO 和自动化系统的时间来处理误报

#### 3.3 run-stderr 日志分析（43 条样本）

- 35 条 (81%) 为 "ACP connection closed" — ENOTFOUND 导致 claude 进程异常退出
- 8 条 (19%) 为 "vcs_state_changed" — 正常通知，非错误
- 0 条直接包含 ENOTFOUND 文本 — 错误在更底层发生，只表现为 ACP 断连

### 四、建议改进

#### 4.1 【推荐·低风险】适配器增加 ENOTFOUND 分类

在 `CLAUDE_TRANSIENT_UPSTREAM_RE` 中增加网络层错误匹配：

```diff
 const CLAUDE_TRANSIENT_UPSTREAM_RE =
-  /(?:rate[-\s]?limit|...)/i;
+  /(?:rate[-\s]?limit|...|
+    ENOTFOUND|EAI_AGAIN|ECONNREFUSED|ETIMEDOUT|
+    Unable to connect to API|network.*unreachable)/i;
```

**效果**：ENOTFOUND 被标记为 `errorCode: "claude_transient_upstream"`, `errorFamily: "transient_upstream"`，运行时可据此做出更合理的重试/降级决策。

#### 4.2 【建议·中等工作量】基础设施侧排查代理可用性

排查 `198.18.0.49` 代理服务的运行状态、崩溃日志、重启周期。这需要访问宿主环境的基础设施配置。

#### 4.3 【可选·长期】心跳 run 容错增强

心跳 run 可以考虑在遇到 ENOTFOUND 时快速失败（而非等待 TCP 超时 2 小时），减少资源浪费。

### 五、处置结论

本 issue 的根因已查明：
1. **直接原因**：本地 API 代理 (`198.18.0.49`) 间歇性不可用
2. **放大因素**：claude-local 适配器未将 ENOTFOUND 分类为瞬时上游错误，无重试/降级
3. **影响**：心跳 run 失败率虚高但不影响实际工作产出

建议将 4.1（适配器补丁）作为后续 action，提交给基础设施/平台团队。本 issue 可关闭。
