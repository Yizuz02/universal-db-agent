import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getPreferences, updatePreferences } from '../services/api';

const PreferencesContext = createContext(null);

const DEFAULTS = {
  theme: 'light', font_size: '16px', font_family: 'system',
  language: 'en', timezone: 'America/Mexico_City', active_credential: null,
};

export function PreferencesProvider({ children }) {
  const [prefs, setPrefs] = useState(() => {
    try { return { ...DEFAULTS, ...JSON.parse(localStorage.getItem('preferences') || '{}') }; }
    catch { return DEFAULTS; }
  });

  // Apply theme + font to <html>
  useEffect(() => {
    document.documentElement.dataset.theme = prefs.theme;
    document.documentElement.dataset.fontFamily = prefs.font_family;
    document.documentElement.style.fontSize = prefs.font_size;
  }, [prefs.theme, prefs.font_family, prefs.font_size]);

  // Load from backend on mount
  useEffect(() => {
    (async () => {
      try {
        const { data } = await getPreferences();
        const merged = {
          theme: data.theme || DEFAULTS.theme,
          font_size: data.font_size || DEFAULTS.font_size,
          font_family: data.font_family || DEFAULTS.font_family,
          language: data.language || DEFAULTS.language,
          timezone: data.timezone || DEFAULTS.timezone,
          active_credential: data.active_credential,
        };
        setPrefs(merged);
        localStorage.setItem('preferences', JSON.stringify(merged));
      } catch { /* keep localStorage */ }
    })();
  }, []);

  const savePrefs = useCallback(async (updates) => {
    const merged = { ...prefs, ...updates };
    setPrefs(merged);
    localStorage.setItem('preferences', JSON.stringify(merged));
    try { await updatePreferences(merged); } catch { /* offline */ }
  }, [prefs]);

  return (
    <PreferencesContext.Provider value={{ prefs, savePrefs }}>
      {children}
    </PreferencesContext.Provider>
  );
}

export const usePreferences = () => useContext(PreferencesContext);
