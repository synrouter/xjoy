# Xjoy 移动端分发方案调研

**日期**: 2026-08-10
**任务**: XJO-282 Week 3 — 分发准备

## 当前状态

### 已有的
- ✅ PWA Manifest (`manifest.json`) — 名称、图标、主题色、方向锁定
- ✅ Apple Meta Tags — `apple-mobile-web-app-capable`, `apple-touch-icon`, `apple-mobile-web-app-title`
- ✅ Viewport Meta Tag — `viewport-fit=cover` 支持 iPhone 安全区域
- ✅ `safe-bottom` CSS 类 — iPhone 底部安全区域适配
- ✅ 移动端响应式设计 (`max-w-lg mx-auto`)

### 缺失的
- ❌ Service Worker — 没有离线缓存能力
- ❌ PWA 安装提示 — 没有引导用户"添加到主屏幕"
- ❌ 原生打包 — 没有 iOS/Android 原生壳

## 推荐分发路径（按优先级）

### 路径 1: PWA 直接分发（推荐优先实施，0 成本，1-2 天）

**适用场景**: 前 100 个热情用户的内测

**需要做的**:
1. 添加 Service Worker（推荐 `@serwist/next` 或 `next-pwa`）
2. 实现 PWA 安装提示 UI（iOS Safari 底部弹窗提示、Android Chrome 自动提示）
3. 部署到 Vercel（免费额度足够）或 Railway

**优势**: 
- 不依赖 Apple Developer / Google Play 审核
- 更新即时（不需要 App Store 审核）
- 用户通过 URL 即可安装

**劣势**:
- iOS 上 PWA 功能受限（无推送通知、存储配额低）
- 用户心智模型：习惯从 App Store 下载

### 路径 2: Capacitor 原生打包 → TestFlight + Google Play（2-4 周，$124 成本）

**适用场景**: 正式对外发布，需要更深度的原生集成

**需要做的**:
1. 安装 Capacitor: `npm install @capacitor/core @capacitor/cli @capacitor/ios @capacitor/android`
2. 配置 `capacitor.config.ts` 指向 Next.js 的 `out` 静态导出目录
3. Next.js 改为静态导出模式 (`output: 'export'`)
4. iOS: Xcode 打包 → App Store Connect → TestFlight
5. Android: Android Studio 打包 → 生成 AAB → Google Play Console

**成本**:
- Apple Developer Program: $99/年
- Google Play Developer: $25（一次性）

**优势**:
- 用户从 App Store / Google Play 下载，信任度高
- 可访问原生 API（推送通知、深度链接等）
- TestFlight 支持最多 10,000 外部测试者

**劣势**:
- App Store 审核可能 1-3 天
- 更新需要重新打包 + 审核

### 路径 3: TWA (Trusted Web Activity) — 仅 Android（1 周，$25 成本）

**适用场景**: Android 用户快速分发，零代码改动即可上架 Google Play

**需要做的**:
1. 使用 `bubblewrap` CLI 生成 TWA 项目
2. 配置 Digital Asset Links（验证网站所有权）
3. 生成 signed AAB → 上传 Google Play

**优势**: 
- 不需要修改现有代码
- 比 PWA 更"原生"的感觉

**劣势**:
- 仅 Android
- 仍需 Google Play 审核

## 针对 XJO-7 (Fly.io) 阻塞的建议

如果 Fly.io 部署持续阻塞，建议：
1. **立即**：部署到 Vercel（PWA 分发），Vercel 免费额度对小规模测试足够
2. **并行**：同时准备 Capacitor 原生打包，为 TestFlight 做准备
3. **回退**：如果部署也阻塞，至少 PWA manifest 已就绪，用户可通过 `localhost` 或 `ngrok` 安装测试

## 推荐立即行动

| 优先级 | 行动 | 预计耗时 |
|-------|------|---------|
| P0 | 添加 Service Worker + PWA 安装提示 | 1 天 |
| P0 | 部署到 Vercel（PWA 测试环境） | 0.5 天 |
| P1 | Capacitor 初始化 + 配置 | 1 天 |
| P1 | Apple Developer 账号注册 | 0.5 天 |
| P2 | TestFlight 构建提交 | 1 天 |
| P2 | Google Play TWA 上架 | 1 天 |

## 结论

对于前 100 个热情用户的内测，**PWA + Vercel 部署**是最快路径。同时在后台推进 Capacitor + TestFlight 准备正式发布。
