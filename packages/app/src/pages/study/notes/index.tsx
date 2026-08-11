/**
 * 笔记列表页面
 *
 * 展示用户所有笔记，支持按书卷过滤、查看详情和删除。
 */

import { useState, useEffect } from 'react';
import Link from 'next/link';
import type { Note } from '@xjoy/shared';
import { fetchNotes, deleteNote, createNote } from '@/lib/api';
import PageHeader from '@/components/ui/PageHeader';

/** 将 "John 3:16" 解析为 { book_name, chapter, verse } */
function parseReference(ref: string): { book_name: string; chapter: number; verse: number } | null {
  const match = ref.trim().match(/^(.+?)\s+(\d+):(\d+)$/);
  if (!match) return null;
  const chapter = parseInt(match[2], 10);
  const verse = parseInt(match[3], 10);
  if (chapter < 1 || chapter > 150 || verse < 1 || verse > 176) return null;
  return { book_name: match[1], chapter, verse };
}

export default function NotesPage() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);

  // 新建笔记表单
  const [showNewForm, setShowNewForm] = useState(false);
  const [newReference, setNewReference] = useState('');
  const [newContent, setNewContent] = useState('');
  const [newSaving, setNewSaving] = useState(false);
  const [newError, setNewError] = useState<string | null>(null);

  useEffect(() => {
    fetchNotes({ limit: 100 })
      .then(setNotes)
      .catch(() => setNotes([]))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await deleteNote(id);
      setNotes((prev) => prev.filter((n) => n.id !== id));
      if (selectedNote?.id === id) setSelectedNote(null);
    } catch {
      // 静默处理
    }
  };

  const handleCreateNote = async () => {
    setNewError(null);
    const parsed = parseReference(newReference.trim());
    if (!parsed) {
      setNewError('请输入正确的经文引用格式，如 "John 3:16"');
      return;
    }
    if (!newContent.trim()) {
      setNewError('请输入笔记内容');
      return;
    }
    setNewSaving(true);
    try {
      const note = await createNote({
        reference: newReference.trim(),
        content: newContent.trim(),
        book_name: parsed.book_name,
        chapter: parsed.chapter,
        verse: parsed.verse,
      });
      setNotes((prev) => [note, ...prev]);
      setShowNewForm(false);
      setNewReference('');
      setNewContent('');
      setNewError(null);
    } catch (e) {
      setNewError('保存失败，请重试');
    } finally {
      setNewSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-parchment-400 text-sm">加载笔记中...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="My Notes"
        subtitle={`${notes.length} ${notes.length === 1 ? 'note' : 'notes'}`}
        bordered
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setNewReference('');
                setNewContent('');
                setNewError(null);
                setShowNewForm(true);
              }}
              className="text-xs bg-accent-500 text-white px-3 py-1.5 rounded-xl hover:bg-accent-600 transition-colors font-medium"
            >
              + 新建笔记
            </button>
            <Link
              href="/study"
              className="text-xs text-parchment-400 hover:text-parchment-600"
            >
              ← Study
            </Link>
          </div>
        }
      />

      <div className="flex-1 overflow-y-auto">
        {notes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full px-5 text-center">
            <span className="text-4xl mb-3">📝</span>
            <p className="text-parchment-600 text-sm font-medium mb-1">
              暂无笔记
            </p>
            <p className="text-parchment-400 text-xs leading-relaxed">
              阅读经文时，点击节号旁的 📝 按钮即可添加笔记。
              <br />
              在此集中管理和回顾你的读经心得。
            </p>
          </div>
        ) : (
          <div className="divide-y divide-parchment-100">
            {notes.map((note) => (
              <div key={note.id} className="px-5 py-4">
                <button
                  onClick={() =>
                    setSelectedNote(
                      selectedNote?.id === note.id ? null : note
                    )
                  }
                  className="w-full text-left"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-parchment-500 mb-1">
                        {note.reference}
                      </p>
                      <p className="text-sm text-parchment-700 line-clamp-2 leading-relaxed">
                        {note.content}
                      </p>
                      <p className="text-[10px] text-parchment-400 mt-1.5">
                        {new Date(note.updated_at).toLocaleDateString('zh-CN', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                    </div>
                    <span className="text-parchment-300 text-xs shrink-0 mt-0.5">
                      {selectedNote?.id === note.id ? '▲' : '▼'}
                    </span>
                  </div>
                </button>

                {/* 展开详情 */}
                {selectedNote?.id === note.id && (
                  <div className="mt-3 pt-3 border-t border-parchment-100">
                    <p className="text-sm text-parchment-700 leading-relaxed whitespace-pre-wrap">
                      {note.content}
                    </p>
                    <div className="flex items-center gap-3 mt-3">
                      <Link
                        href={`/bible/${encodeURIComponent(note.book_name)}/${note.chapter}#v${note.verse}`}
                        className="text-xs text-parchment-500 hover:text-parchment-700 underline underline-offset-2"
                      >
                        Read verse →
                      </Link>
                      <button
                        onClick={() => handleDelete(note.id)}
                        className="text-xs text-red-400 hover:text-red-600"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 新建笔记对话框 */}
      {showNewForm && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/30" onClick={() => setShowNewForm(false)}>
          <div
            className="bg-white rounded-t-2xl sm:rounded-2xl w-full sm:max-w-md p-5 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-lg font-semibold text-parchment-800 mb-4">
              新建笔记
            </h2>

            {/* 经文引用 */}
            <label className="block text-xs font-medium text-parchment-500 mb-1">
              经文引用
            </label>
            <input
              value={newReference}
              onChange={(e) => {
                setNewReference(e.target.value);
                setNewError(null);
              }}
              placeholder='例如 "John 3:16"'
              className="w-full bg-parchment-50 border border-parchment-200 rounded-lg px-3 py-2.5 text-sm text-parchment-700 placeholder-parchment-300 focus:outline-none focus:border-accent-400 focus:ring-2 focus:ring-accent-500/10 mb-3"
            />

            {/* 笔记内容 */}
            <label className="block text-xs font-medium text-parchment-500 mb-1">
              笔记内容
            </label>
            <textarea
              value={newContent}
              onChange={(e) => {
                setNewContent(e.target.value);
                setNewError(null);
              }}
              placeholder="写下你对这节经文的思考和心得..."
              className="w-full bg-parchment-50 border border-parchment-200 rounded-lg px-3 py-2.5 text-sm text-parchment-700 placeholder-parchment-300 focus:outline-none focus:border-accent-400 focus:ring-2 focus:ring-accent-500/10 resize-none mb-3"
              rows={4}
              autoFocus
            />

            {newError && (
              <p className="text-xs text-red-500 mb-2">{newError}</p>
            )}

            <div className="flex items-center justify-end gap-2">
              <button
                onClick={() => setShowNewForm(false)}
                className="text-sm text-parchment-500 hover:text-parchment-700 px-3 py-2"
              >
                取消
              </button>
              <button
                onClick={handleCreateNote}
                disabled={newSaving}
                className="text-sm bg-accent-500 text-white px-4 py-2 rounded-lg hover:bg-accent-600 disabled:opacity-40 transition-colors font-medium"
              >
                {newSaving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
