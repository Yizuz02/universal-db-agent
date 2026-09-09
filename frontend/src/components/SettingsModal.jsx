import { useState, useEffect, useRef } from 'react';
import { useI18n } from '../context/I18nContext';
import { usePreferences } from '../context/PreferencesContext';
import { getCredentialOptions, getCredentials, createCredential, updateCredential, deleteCredential, activateCredential } from '../services/api';

const TABS = ['general', 'appearance', 'llm', 'database'];
const THEMES = ['light', 'dark', 'ocean', 'matrix', 'sunset', 'blush', 'synthwave', 'graphite'];
const THEME_COLORS = {
  light: '#f1f5f9,#0891b2', dark: '#0f172a,#22d3ee', ocean: '#eff6ff,#2563eb', matrix: '#0d1117,#00ff41',
  sunset: '#fffbeb,#f97316', blush: '#fff1f2,#e11d48', synthwave: '#1a1b2e,#bb9af7', graphite: '#f5f5f4,#78716c',
};
const FONT_SIZES = ['12px', '14px', '16px', '18px'];
const FONT_FAMILIES = [
  { id: 'system', label: 'System UI', font: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", sans-serif' },
  { id: 'serif', label: 'Serif', font: 'Georgia, "Times New Roman", serif' },
  { id: 'mono', label: 'Monospace', font: '"JetBrains Mono", "Fira Code", Consolas, monospace' },
  { id: 'rounded', label: 'Rounded', font: 'Nunito, Quicksand, system-ui, sans-serif' },
];
const LANGUAGES = [
  { id: 'en', label: '🇬🇧 English' }, { id: 'es', label: '🇲🇽 Español' },
  { id: 'zh', label: '🇨🇳 中文' }, { id: 'pt', label: '🇧🇷 Português' },
];
const ICONS = { general: 'settings', appearance: 'palette', llm: 'psychology', database: 'storage' };

export default function SettingsModal({ onClose }) {
  const { t, lang, changeLang } = useI18n();
  const { prefs, savePrefs } = usePreferences();
  const [tab, setTab] = useState('general');
  const [creds, setCreds] = useState([]);
  const [options, setOptions] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({ name: '', provider_type: 'openai', model: '', api_key: '', base_url: '', temperature: 0, max_tokens: 4096, scope: 'personal', group: '' });
  const modalRef = useRef();

  useEffect(() => {
    if (tab === 'llm') {
      getCredentialOptions().then(r => setOptions(r.data)).catch(() => {});
      loadCreds();
    }
  }, [tab]);

  const loadCreds = async () => {
    try {
      const { data } = await getCredentials();
      setCreds(data);
    } catch {}
  };

  const close = (e) => { if (e.target === modalRef.current) onClose(); };

  const selectTheme = (theme) => savePrefs({ theme });
  const selectSize = (size) => savePrefs({ font_size: size });
  const selectFamily = (family) => savePrefs({ font_family: family });
  const selectLang = (l) => { changeLang(l); savePrefs({ language: l }); };
  const selectTz = (tz) => savePrefs({ timezone: tz });

  const newForm = () => {
    setEditingId(null);
    setForm({ name: '', provider_type: 'openai', model: options?.providers?.[0]?.models?.[0] || '', api_key: '', base_url: options?.providers?.find(p => p.id === 'ollama')?.default_base_url || '', temperature: 0, max_tokens: 4096, scope: 'personal', group: '' });
    setShowForm(true);
  };

  const saveCred = async () => {
    const payload = { ...form };
    if (payload.scope === 'group' && payload.group) {
      payload.group = parseInt(payload.group);
    } else {
      delete payload.group;
    }
    try {
      if (editingId) await updateCredential(editingId, payload);
      else await createCredential(payload);
      setShowForm(false);
      loadCreds();
    } catch (e) { alert('Error saving credential'); }
  };

  const handleProviderChange = (pid) => {
    const prov = options?.providers?.find(p => p.id === pid);
    setForm(f => ({ ...f, provider_type: pid, model: prov?.models?.[0] || '', base_url: prov?.default_base_url || '' }));
  };

  const Btn = ({ active, onClick, children }) => (
    <button onClick={onClick}
      className={`rounded-lg px-3 py-2 text-xs font-medium border transition ${active ? 'btn-active' : 'btn-inactive'}`}>
      {children}
    </button>
  );

  return (
    <div ref={modalRef} onClick={close}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="mx-4 flex h-[85vh] w-full max-w-3xl flex-col rounded-2xl border shadow-2xl" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
        {/* Header */}
        <div className="flex shrink-0 items-center justify-between border-b px-6 py-4" style={{ borderColor: 'var(--color-border)' }}>
          <h2 className="text-xl font-semibold" style={{ color: 'var(--color-text)' }}>{t('settings.title')}</h2>
          <button onClick={onClose} className="rounded-lg p-2 transition hover:bg-page" style={{ color: 'var(--color-text-muted)' }}>
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>
        <div className="flex flex-1 overflow-hidden">
          {/* Tabs */}
          <nav className="flex w-48 shrink-0 flex-col gap-1 border-r p-3" style={{ borderColor: 'var(--color-border)' }}>
            {TABS.map(tabId => (
              <button key={tabId} onClick={() => setTab(tabId)}
                className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition ${tab === tabId ? 'btn-active' : 'btn-inactive'}`}>
                <span className="material-symbols-outlined text-lg">{ICONS[tabId]}</span>
                <span>{t(`tab.${tabId}`)}</span>
              </button>
            ))}
          </nav>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6" style={{ color: 'var(--color-text)' }}>
            {/* GENERAL */}
            {tab === 'general' && (
              <div>
                <h3 className="mb-5 text-lg font-semibold">{t('general.language')}</h3>
                <div className="mb-6">
                  <div className="grid grid-cols-2 gap-2">
                    {LANGUAGES.map(l => (
                      <Btn key={l.id} active={lang === l.id} onClick={() => selectLang(l.id)}>{l.label}</Btn>
                    ))}
                  </div>
                </div>
                <h3 className="mb-3 text-lg font-semibold">{t('general.timezone')}</h3>
                <select value={prefs.timezone} onChange={(e) => selectTz(e.target.value)}
                  className="w-full rounded-xl border px-4 py-3 text-sm outline-none" style={{ backgroundColor: 'var(--color-page)', borderColor: 'var(--color-border)', color: 'var(--color-text)' }}>
                  {['America/Mexico_City', 'America/New_York', 'America/Chicago', 'Europe/Madrid', 'Europe/London', 'Asia/Tokyo', 'Asia/Shanghai', 'UTC'].map(z => (
                    <option key={z} value={z}>{z}</option>
                  ))}
                </select>
              </div>
            )}

            {/* APPEARANCE */}
            {tab === 'appearance' && (
              <div>
                <h3 className="mb-5 text-lg font-semibold">{t('appearance.theme')}</h3>
                <div className="mb-6 grid grid-cols-4 gap-2">
                  {THEMES.map(th => (
                    <button key={th} onClick={() => selectTheme(th)}
                      className={`flex flex-col items-center gap-1 rounded-lg border px-2 py-3 text-xs font-medium transition ${prefs.theme === th ? 'btn-active' : 'btn-inactive'}`}>
                      <span className="mb-0.5 flex h-6 w-full max-w-[40px] rounded-sm" style={{ background: `linear-gradient(135deg, ${THEME_COLORS[th]})` }}></span>
                      <span>{th.charAt(0).toUpperCase() + th.slice(1)}</span>
                    </button>
                  ))}
                </div>
                <h3 className="mb-3 text-lg font-semibold">{t('appearance.font_size')}</h3>
                <div className="mb-6 flex gap-2">
                  {FONT_SIZES.map(s => (
                    <Btn key={s} active={prefs.font_size === s} onClick={() => selectSize(s)}
                      style={{ fontSize: s }}>{s}</Btn>
                  ))}
                </div>
                <h3 className="mb-3 text-lg font-semibold">{t('appearance.font_family')}</h3>
                <div className="grid grid-cols-2 gap-2">
                  {FONT_FAMILIES.map(f => (
                    <button key={f.id} onClick={() => selectFamily(f.id)}
                      className={`rounded-xl border px-4 py-3 text-sm font-medium transition text-left ${prefs.font_family === f.id ? 'btn-active' : 'btn-inactive'}`}
                      style={{ fontFamily: f.font }}>{f.label}</button>
                  ))}
                </div>
              </div>
            )}

            {/* LLM */}
            {tab === 'llm' && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">Models</h3>
                  <button onClick={newForm} className="btn-primary rounded-lg px-3 py-1.5 text-xs font-medium">+ Add Model</button>
                </div>
                {creds.length === 0 && <p className="text-xs text-center py-4" style={{ color: 'var(--color-text-muted)' }}>No models saved yet.</p>}
                {creds.map(c => (
                  <div key={c.id} className="flex items-center justify-between rounded-lg border p-3 mb-2" style={{ borderColor: 'var(--color-border)' }}>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{c.name}</span>
                        <span className="rounded-full px-2 py-0.5 text-xs" style={{ backgroundColor: 'var(--color-page)', color: 'var(--color-text-muted)' }}>{c.provider_type}</span>
                      </div>
                      <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{c.model}</p>
                    </div>
                    <div className="flex gap-1">
                      <button onClick={async () => { await activateCredential(c.id); loadCreds(); }}
                        className={`rounded-lg px-2.5 py-1 text-xs font-medium ${c.is_active ? 'btn-active' : 'btn-inactive'}`}>
                        {c.is_active ? 'Active' : 'Activate'}
                      </button>
                      <button onClick={() => { setEditingId(c.id); setForm(c); setShowForm(true); }} className="btn-inactive rounded-lg px-2 py-1 text-xs">✏️</button>
                      <button onClick={async () => { if (confirm('Delete?')) { await deleteCredential(c.id); loadCreds(); }}} className="btn-inactive rounded-lg px-2 py-1 text-xs">🗑️</button>
                    </div>
                  </div>
                ))}
                {showForm && (
                  <div className="rounded-xl border p-4 space-y-3 mt-4" style={{ borderColor: 'var(--color-border)' }}>
                    <div className="flex justify-between"><h4 className="text-sm font-semibold">{editingId ? 'Edit' : 'Add'} Model</h4>
                      <button onClick={() => setShowForm(false)} className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Cancel</button></div>
                    <Input label="Name" value={form.name} onChange={(v) => setForm(f => ({ ...f, name: v }))} placeholder="My OpenAI key" />
                    <div>
                      <label className="mb-1 block text-xs font-medium">Provider</label>
                      <select value={form.provider_type} onChange={(e) => handleProviderChange(e.target.value)}
                        className="w-full rounded-lg border px-3 py-2 text-sm outline-none" style={{ backgroundColor: 'var(--color-page)', borderColor: 'var(--color-border)', color: 'var(--color-text)' }}>
                        {options?.providers?.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="mb-1 block text-xs font-medium">Model</label>
                      <select value={form.model} onChange={(v) => setForm(f => ({ ...f, model: v.target.value }))}
                        className="w-full rounded-lg border px-3 py-2 text-sm outline-none" style={{ backgroundColor: 'var(--color-page)', borderColor: 'var(--color-border)', color: 'var(--color-text)' }}>
                        {options?.providers?.find(p => p.id === form.provider_type)?.models?.map(m => <option key={m} value={m}>{m}</option>)}
                      </select>
                    </div>
                    {options?.providers?.find(p => p.id === form.provider_type)?.has_api_key !== false && (
                      <Input label="API Key" type="password" value={form.api_key} onChange={(v) => setForm(f => ({ ...f, api_key: v }))} placeholder="sk-..." />
                    )}
                    {options?.providers?.find(p => p.id === form.provider_type)?.has_base_url && (
                      <Input label="Base URL" value={form.base_url} onChange={(v) => setForm(f => ({ ...f, base_url: v }))} placeholder="http://localhost:11434" />
                    )}
                    <details className="group">
                      <summary className="cursor-pointer text-xs font-medium" style={{ color: 'var(--color-text-muted)' }}>
                        <span className="inline-flex items-center gap-1">
                          <span className="material-symbols-outlined text-sm transition group-open:rotate-90">chevron_right</span>
                          Advanced Settings
                        </span>
                      </summary>
                      <div className="mt-3 grid grid-cols-2 gap-3">
                        <div><label className="mb-1 block text-xs font-medium">Temperature</label>
                          <input type="number" step="0.1" min="0" max="2" value={form.temperature} onChange={(e) => setForm(f => ({ ...f, temperature: e.target.value }))}
                            className="w-full rounded-lg border px-3 py-2 text-sm outline-none" style={{ backgroundColor: 'var(--color-page)', borderColor: 'var(--color-border)', color: 'var(--color-text)' }} /></div>
                        <div><label className="mb-1 block text-xs font-medium">Max Tokens</label>
                          <input type="number" min="1" value={form.max_tokens} onChange={(e) => setForm(f => ({ ...f, max_tokens: e.target.value }))}
                            className="w-full rounded-lg border px-3 py-2 text-sm outline-none" style={{ backgroundColor: 'var(--color-page)', borderColor: 'var(--color-border)', color: 'var(--color-text)' }} /></div>
                      </div>
                    </details>
                    <div>
                      <label className="mb-1 block text-xs font-medium">Scope</label>
                      <div className="flex items-center gap-3">
                        {['personal', 'group'].map(s => (
                          <label key={s} className="flex items-center gap-1.5 cursor-pointer">
                            <input type="radio" name="scope" value={s} checked={form.scope === s} onChange={() => setForm(f => ({ ...f, scope: s }))} />
                            <span className="text-xs">{s === 'personal' ? '🔒 Personal' : '👥 Group'}</span>
                          </label>
                        ))}
                        <select disabled={form.scope !== 'group'} value={form.group} onChange={(e) => setForm(f => ({ ...f, group: e.target.value }))}
                          className="flex-1 rounded-lg border px-2 py-1.5 text-xs outline-none" style={{ backgroundColor: 'var(--color-page)', borderColor: 'var(--color-border)', color: 'var(--color-text)' }}>
                          <option value="">Select group...</option>
                          {options?.groups?.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
                        </select>
                      </div>
                    </div>
                    <button onClick={saveCred} className="btn-primary w-full rounded-lg py-2 text-sm font-medium">Save Model</button>
                  </div>
                )}
              </div>
            )}

            {/* DATABASE placeholder */}
            {tab === 'database' && (
              <div>
                <h3 className="mb-5 text-lg font-semibold">{t('db.path')}</h3>
                <div className="space-y-4 opacity-40 pointer-events-none">
                  <div><label className="mb-2 block text-sm font-medium">{t('db.path')}</label>
                    <div className="rounded-xl border px-4 py-3 text-sm font-mono" style={{ backgroundColor: 'var(--color-page)', borderColor: 'var(--color-border)', color: 'var(--color-text-muted)' }}>storage/databases/construction_company.db</div></div>
                  <div><label className="mb-2 block text-sm font-medium">{t('db.status')}</label>
                    <div className="flex items-center gap-2 rounded-xl border px-4 py-3 text-sm" style={{ backgroundColor: 'var(--color-page)', borderColor: 'var(--color-border)' }}>
                      <span className="h-2 w-2 rounded-full bg-green-500"></span>
                      <span style={{ color: 'var(--color-text-muted)' }}>{t('db.connected')}</span></div></div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Input({ label, type = 'text', value, onChange, placeholder }) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium" style={{ color: 'var(--color-text)' }}>{label}</label>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
        className="w-full rounded-lg border px-3 py-2 text-sm outline-none"
        style={{ backgroundColor: 'var(--color-page)', borderColor: 'var(--color-border)', color: 'var(--color-text)' }} />
    </div>
  );
}
