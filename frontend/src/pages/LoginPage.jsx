import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await login(username, password);
      navigate('/chat');
    } catch {
      setError('Invalid credentials');
    }
  };

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: 'var(--color-page)' }}>
      <div className="hidden lg:flex lg:w-1/2 items-center justify-center" style={{ backgroundColor: 'var(--color-primary)' }}>
        <div className="max-w-md" style={{ color: 'var(--color-primary-foreground)' }}>
          <h1 className="text-5xl font-bold mb-6" style={{ color: 'inherit' }}>{t('login.title')}</h1>
          <p className="text-lg leading-relaxed" style={{ color: 'var(--color-primary-subtle)' }}>{t('login.subtitle')}</p>
        </div>
      </div>
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <div className="rounded-2xl shadow-xl p-10" style={{ backgroundColor: 'var(--color-surface)' }}>
            <h2 className="text-3xl font-bold" style={{ color: 'var(--color-text)' }}>{t('login.welcome')}</h2>
            <p className="mt-2 mb-8" style={{ color: 'var(--color-text-muted)' }}>{t('login.sign_in_prompt')}</p>
            {error && <p className="mb-4 text-sm text-red-500">{error}</p>}
            <form onSubmit={handleSubmit}>
              <div className="mb-5">
                <label className="block mb-2 text-sm font-medium" style={{ color: 'var(--color-text)' }}>{t('login.username')}</label>
                <input type="text" value={username} onChange={(e) => setUsername(e.target.value)}
                  className="w-full rounded-xl border px-4 py-3 outline-none focus:ring-2"
                  style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-surface)', color: 'var(--color-text)' }} />
              </div>
              <div className="mb-8">
                <label className="block mb-2 text-sm font-medium" style={{ color: 'var(--color-text)' }}>{t('login.password')}</label>
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border px-4 py-3 outline-none focus:ring-2"
                  style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-surface)', color: 'var(--color-text)' }} />
              </div>
              <button type="submit"
                className="btn-primary w-full rounded-xl py-3 font-semibold transition-colors">
                {t('login.sign_in')}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
