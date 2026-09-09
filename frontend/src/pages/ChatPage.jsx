import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import {
  getConversations,
  createConversation,
  getConversation,
  sendMessage,
  updateConversationTitle,
  deleteConversation,
  getFilePreview,
  downloadFile,
} from '../services/api';
import SettingsModal from '../components/SettingsModal';
import FilesModal from '../components/FilesModal';

export default function ChatPage() {
  const { user } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  const [modalOpen, setModalOpen] = useState(false);
  const [filesOpen, setFilesOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);

  const [previewData, setPreviewData] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState('');

  const inputRef = useRef(null);
  const bottomRef = useRef(null);
  const tmpId = useRef(0);

  useEffect(() => { if (!user) navigate('/login'); }, [user, navigate]);

  // Load the conversation list on mount; select the most recent one.
  const loadConversations = useCallback(async () => {
    try {
      const { data } = await getConversations();
      setConversations(data);
      setActiveId(prev => prev ?? data[0]?.id ?? null);
    } catch {
      setError(t('chat.load_failed'));
    }
  }, [t]);

  useEffect(() => { loadConversations(); }, [loadConversations]);

  // Load history whenever the active conversation changes.
  useEffect(() => {
    if (!activeId) { setMessages([]); return; }
    let cancelled = false;
    setHistoryLoading(true);
    getConversation(activeId)
      .then(({ data }) => { if (!cancelled) setMessages(data.messages || []); })
      .catch(() => { if (!cancelled) setError(t('chat.load_failed')); })
      .finally(() => { if (!cancelled) setHistoryLoading(false); });
    return () => { cancelled = true; };
  }, [activeId, t]);

  // Keep the latest message in view.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  const resizeInput = () => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  };

  // Auto-grow/shrink the textarea after every input change (runs post-render).
  useEffect(() => { resizeInput(); }, [input]);

  const handleNewConversation = async () => {
    try {
      const { data } = await createConversation();
      setConversations(cs => [data, ...cs]);
      setActiveId(data.id);
      setMessages([]);
      setError('');
    } catch {
      setError(t('chat.load_failed'));
    }
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || sending || !activeId) return;
    setInput('');
    setError('');
    const userMsg = { id: `tmp-${++tmpId.current}`, role: 'user', content: text, created_at: new Date().toISOString() };
    setMessages(ms => [...ms, userMsg]);
    setSending(true);
    try {
      const { data } = await sendMessage(activeId, text);
      setMessages(ms => [...ms, { id: `tmp-${++tmpId.current}`, role: 'agent', content: data.agent_response, files: data.files || [], created_at: new Date().toISOString() }]);
      setConversations(cs => {
        const conv = cs.find(c => c.id === activeId);
        if (!conv) return cs;
        const updated = { ...conv, updated_at: new Date().toISOString() };
        if (data.title) updated.title = data.title;
        return [updated, ...cs.filter(c => c.id !== activeId)];
      });
    } catch {
      setError(t('chat.send_failed'));
      setInput(text);
      setMessages(ms => ms.filter(m => m !== userMsg));
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleRenameClick = (e, conv) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditTitle(conv.title);
  };

  const handleRenameCommit = async (id) => {
    const title = editTitle.trim();
    setEditingId(null);
    setEditTitle('');
    const current = conversations.find(c => c.id === id);
    if (!title || title === current?.title) return;
    try {
      const { data } = await updateConversationTitle(id, title);
      setConversations(cs => cs.map(c => c.id === id ? { ...c, title: data.title } : c));
    } catch {
      setError(t('chat.load_failed'));
    }
  };

  const handleRenameCancel = () => {
    setEditingId(null);
    setEditTitle('');
  };

  const handlePreview = async (fileId) => {
    setPreviewLoading(true);
    setPreviewError('');
    setPreviewData(null);
    try {
      const { data } = await getFilePreview(fileId);
      setPreviewData(data);
    } catch {
      setPreviewError(t('file.preview_error'));
    } finally {
      setPreviewLoading(false);
    }
  };

  const closePreview = () => {
    setPreviewData(null);
    setPreviewError('');
  };

  const handleDeleteClick = (e, id) => {
    e.stopPropagation();
    setDeleteConfirmId(id);
  };

  const handleDeleteConfirm = async () => {
    const id = deleteConfirmId;
    setDeleteConfirmId(null);
    try {
      await deleteConversation(id);
      setConversations(cs => cs.filter(c => c.id !== id));
      if (id === activeId) {
        setActiveId(null);
        setMessages([]);
      }
    } catch {
      setError(t('chat.load_failed'));
    }
  };

  const handleRenameKeyDown = (e, id) => {
    if (e.key === 'Enter') { e.preventDefault(); handleRenameCommit(id); }
    if (e.key === 'Escape') { e.preventDefault(); handleRenameCancel(); }
  };

  if (!user) return null;

  const pageBg = 'var(--color-page)';
  const surfaceBg = 'var(--color-surface)';
  const borderColor = 'var(--color-border)';
  const textColor = 'var(--color-text)';
  const mutedColor = 'var(--color-text-muted)';
  const activeConv = conversations.find(c => c.id === activeId);
  const canSend = !sending && !!input.trim() && !!activeId;

  return (
    <div className="flex h-screen" style={{ backgroundColor: pageBg }}>
      {/* Sidebar */}
      <div className={`flex flex-col border-r overflow-hidden transition-all duration-300 ${sidebarOpen ? 'w-80' : 'w-16'}`}
        style={{ backgroundColor: surfaceBg, borderColor }}>
        <div className="flex h-16 items-center justify-between px-5">
          {sidebarOpen && <h1 className="text-xl font-bold" style={{ color: textColor }}>{t('sidebar.app_title')}</h1>}
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="rounded-lg p-2 transition hover:bg-page">
            <span className="material-symbols-outlined">menu</span>
          </button>
        </div>
        {sidebarOpen && (
          <div className="flex flex-1 flex-col">
            <div className="px-5 pb-4">
              <button onClick={handleNewConversation}
                className="btn-primary w-full rounded-xl py-3 font-medium transition">
                {t('sidebar.new_conversation')}
              </button>
            </div>
            <div className="px-5 pb-5">
              <input type="text" placeholder={t('sidebar.search')}
                className="w-full rounded-xl border px-4 py-3 outline-none text-sm"
                style={{ borderColor, backgroundColor: 'var(--color-page)', color: textColor }} />
            </div>
            <div className="flex-1 overflow-y-auto px-2">
              <p className="px-3 py-2 text-xs" style={{ color: mutedColor }}>TODAY</p>
              {conversations.map(c => (
                <button key={c.id} onClick={() => setActiveId(c.id)}
                  className={`group mb-1 flex w-full items-center rounded-xl px-4 py-3 text-sm transition ${c.id === activeId ? 'btn-active' : 'hover:bg-page'}`}
                  style={c.id === activeId ? undefined : { color: textColor }}>
                  <span className="material-symbols-outlined mr-3 text-lg shrink-0">chat_bubble_outline</span>
                  {editingId === c.id ? (
                    <input
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onKeyDown={(e) => handleRenameKeyDown(e, c.id)}
                      onBlur={() => handleRenameCommit(c.id)}
                      className="flex-1 rounded-lg border bg-transparent px-2 py-1 text-sm outline-none"
                      style={{ borderColor, color: textColor }}
                      autoFocus
                      maxLength={255}
                    />
                  ) : (
                    <>
                      <span className="truncate flex-1 text-left">{c.title}</span>
                      <span className="ml-2 flex shrink-0 items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                        <span
                          className="material-symbols-outlined rounded p-0.5 text-base hover:opacity-70"
                          onClick={(e) => handleRenameClick(e, c)}
                          title={t('sidebar.rename')}>edit</span>
                        <span
                          className="material-symbols-outlined rounded p-0.5 text-base hover:opacity-70"
                          onClick={(e) => handleDeleteClick(e, c.id)}
                          title={t('sidebar.delete')}>delete</span>
                      </span>
                    </>
                  )}
                </button>
              ))}
            </div>
            <div className="border-t p-3" style={{ borderColor }}>
              <button onClick={() => setFilesOpen(true)}
                className="mb-2 flex w-full items-center rounded-xl px-4 py-3 transition hover:bg-page"
                style={{ color: textColor }}>
                <span className="material-symbols-outlined">folder_open</span>
                {sidebarOpen && <span className="ml-3">Files</span>}
              </button>
              <button onClick={() => setModalOpen(true)}
                className="mb-2 flex w-full items-center rounded-xl px-4 py-3 transition hover:bg-page"
                style={{ color: textColor }}>
                <span className="material-symbols-outlined">settings</span>
                {sidebarOpen && <span className="ml-3">{t('sidebar.settings')}</span>}
              </button>
              <div className="flex items-center rounded-xl px-4 py-3" style={{ color: mutedColor }}>
                <span className="material-symbols-outlined">account_circle</span>
                {sidebarOpen && <span className="ml-3">{user?.username}</span>}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main area */}
      <div className="flex flex-1 flex-col">
        {/* Header */}
        <div className="flex h-16 items-center justify-between border-b px-6" style={{ borderColor }}>
          <h2 className="truncate text-xl font-semibold" style={{ color: textColor }}>
            {activeConv?.title ?? t('header.new_chat')}
          </h2>
          <span className="text-sm" style={{ color: mutedColor }}>{user?.username}</span>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-8 py-6">
          {messages.length === 0 ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <h1 className="mb-3 text-4xl font-bold" style={{ color: textColor }}>Universal DB Agent</h1>
                <p className="max-w-xl" style={{ color: mutedColor }}>{t('chat.empty_subtitle')}</p>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {messages.map(m => {
                if (m.has_tool_calls) {
                  return (
                    <div key={m.id} className="flex justify-start">
                      <div className="flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs italic" style={{ color: mutedColor }}>
                        <span className="material-symbols-outlined text-sm">build</span>
                        {m.content}
                      </div>
                    </div>
                  );
                }
                const isUser = m.role === 'user';
                return (
                  <div key={m.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                    <div className={`md ${isUser ? 'md-on-primary' : ''} max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed`}
                      style={isUser
                        ? { backgroundColor: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }
                        : { backgroundColor: surfaceBg, color: textColor, border: `1px solid ${borderColor}` }}>
                      <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
                        {m.content}
                      </ReactMarkdown>
                      {m.files && m.files.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {m.files.map(f => (
                            <div key={f.id} className="flex items-center gap-2 rounded-lg border px-3 py-2 text-xs"
                              style={{ borderColor, backgroundColor: 'var(--color-page)' }}>
                              <span className="material-symbols-outlined text-base">
                                {f.extension === 'md' ? 'description' : (f.extension === 'csv' || f.extension === 'xlsx') ? 'table_chart' : 'insert_drive_file'}
                              </span>
                              <span className="font-medium" style={{ color: textColor }}>{f.filename}</span>
                              <button onClick={() => handlePreview(f.id)} className="ml-1 rounded p-1 hover:brightness-110"
                                style={{ color: mutedColor }} title={t('file.preview')}>
                                <span className="material-symbols-outlined text-sm">visibility</span>
                              </button>
                              <button onClick={() => downloadFile(f.id)} className="rounded p-1 hover:brightness-110"
                                style={{ color: mutedColor }} title={t('file.download')}>
                                <span className="material-symbols-outlined text-sm">download</span>
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
              {sending && (
                <div className="flex justify-start">
                  <div className="flex items-center gap-2 rounded-2xl border px-4 py-3 text-sm animate-pulse"
                    style={{ backgroundColor: surfaceBg, color: mutedColor, borderColor }}>
                    <span className="material-symbols-outlined text-base">auto_awesome</span>
                    {t('chat.thinking')}
                  </div>
                </div>
              )}
              {historyLoading && (
                <div className="flex justify-center py-4 text-xs" style={{ color: mutedColor }}>
                  Loading...
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t p-6" style={{ borderColor }}>
          {error && <p className="mb-3 text-sm text-red-500">{error}</p>}
          <div className="flex items-end rounded-2xl border p-3" style={{ borderColor, backgroundColor: surfaceBg }}>
            <textarea
              ref={inputRef}
              rows="1"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t('chat_input.placeholder')}
              className="max-h-[200px] flex-1 resize-none bg-transparent py-2 leading-6 outline-none text-sm"
              style={{ color: textColor }} />
            <button onClick={handleSend} disabled={!canSend}
              className="btn-primary ml-4 flex h-11 w-11 shrink-0 items-center justify-center rounded-full transition-colors disabled:opacity-50">
              <span className="material-symbols-outlined">arrow_upward</span>
            </button>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirmId != null && (
        <div onClick={() => setDeleteConfirmId(null)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="mx-4 w-full max-w-md rounded-2xl border p-6 shadow-2xl"
            style={{ backgroundColor: surfaceBg, borderColor }}
            onClick={e => e.stopPropagation()}>
            <h3 className="mb-2 text-lg font-semibold" style={{ color: textColor }}>{t('sidebar.confirm_delete_title')}</h3>
            <p className="mb-6 text-sm" style={{ color: mutedColor }}>{t('sidebar.confirm_delete_message')}</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteConfirmId(null)}
                className="rounded-xl border px-4 py-2 text-sm font-medium transition hover:brightness-110"
                style={{ borderColor, backgroundColor: 'var(--color-page)', color: textColor }}>
                {t('sidebar.cancel')}
              </button>
              <button onClick={handleDeleteConfirm}
                className="btn-primary rounded-xl px-4 py-2 text-sm font-medium transition">
                {t('sidebar.delete')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Settings Modal */}
      {modalOpen && <SettingsModal onClose={() => setModalOpen(false)} />}

      {/* Files Modal */}
      {filesOpen && <FilesModal onClose={() => setFilesOpen(false)} />}

      {/* Preview Modal */}
      {(previewData || previewLoading || previewError) && (
        <div onClick={closePreview}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="mx-4 w-full max-w-4xl max-h-[80vh] overflow-y-auto rounded-2xl border p-6 shadow-2xl"
            style={{ backgroundColor: surfaceBg, borderColor }}
            onClick={e => e.stopPropagation()}>
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold" style={{ color: textColor }}>{t('file.preview')}</h3>
              <button onClick={closePreview}
                className="rounded-lg p-1 transition hover:brightness-110" style={{ color: mutedColor }}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            {previewLoading && <p style={{ color: mutedColor }}>{t('file.loading')}</p>}
            {previewError && <p className="text-red-500">{previewError}</p>}
            {previewData && previewData.type === 'markdown' && (
              <div className="md p-4 rounded-xl" style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-page)' }}>
                <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>{previewData.content}</ReactMarkdown>
              </div>
            )}
            {(previewData && (previewData.type === 'csv' || previewData.type === 'excel')) && (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-sm" style={{ color: textColor }}>
                  <thead>
                    <tr>
                      {previewData.headers.map((h, i) => (
                        <th key={i} className="border px-3 py-2 text-left font-semibold" style={{ borderColor, backgroundColor: 'var(--color-page)' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.rows.map((row, ri) => (
                      <tr key={ri}>
                        {row.map((cell, ci) => (
                          <td key={ci} className="border px-3 py-1.5" style={{ borderColor }}>{cell}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
