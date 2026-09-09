import { createContext, useContext, useState, useEffect } from 'react';
import I18N from '../i18n';

const I18nContext = createContext(null);

export function I18nProvider({ children }) {
  const [lang, setLang] = useState(() => {
    try {
      const p = JSON.parse(localStorage.getItem('preferences') || '{}');
      return p.language || 'en';
    } catch { return 'en'; }
  });

  const t = (key) => (I18N[lang] || I18N.en)[key] || key;

  const changeLang = (l) => {
    setLang(l);
    document.documentElement.lang = l === 'zh' ? 'zh-CN' : l === 'pt' ? 'pt-BR' : l;
  };

  useEffect(() => {
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : lang === 'pt' ? 'pt-BR' : lang;
  }, [lang]);

  return (
    <I18nContext.Provider value={{ lang, t, changeLang }}>
      {children}
    </I18nContext.Provider>
  );
}

export const useI18n = () => useContext(I18nContext);
