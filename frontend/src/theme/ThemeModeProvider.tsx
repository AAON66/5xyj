import React, { createContext, useState, useEffect, useCallback } from 'react';

export type ThemeMode = 'light' | 'dark';

export interface ThemeModeContextValue {
  mode: ThemeMode;
  isDark: boolean;
  toggleMode: () => void;
  setMode: (m: ThemeMode) => void;
}

export const ThemeModeContext = createContext<ThemeModeContextValue | null>(null);

const STORAGE_KEY = 'theme-mode';

function readInitialMode(): ThemeMode {
  if (typeof window === 'undefined') return 'light';
  // Read from data-theme set by FOUC script in index.html (single source of truth)
  const htmlTheme = document.documentElement.getAttribute('data-theme');
  if (htmlTheme === 'light' || htmlTheme === 'dark') return htmlTheme;
  // Fallback: localStorage > matchMedia > 'light'
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'light' || saved === 'dark') return saved;
  } catch {
    // Safari private mode may throw
  }
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function ThemeModeProvider({ children }: React.PropsWithChildren) {
  const [mode, setModeState] = useState<ThemeMode>(readInitialMode);

  const setMode = useCallback((m: ThemeMode) => {
    setModeState(m);
  }, []);

  const toggleMode = useCallback(() => {
    setModeState((prev) => (prev === 'light' ? 'dark' : 'light'));
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', mode);
    try {
      localStorage.setItem(STORAGE_KEY, mode);
    } catch {
      // Safari private mode may throw
    }
    // Sync html/body background to prevent FOUC script stale backgrounds
    if (mode === 'dark') {
      document.documentElement.style.backgroundColor = '#1F1F1F';
      document.body.style.backgroundColor = '#1F1F1F';
    } else {
      document.documentElement.style.backgroundColor = '';
      document.body.style.backgroundColor = '';
    }
  }, [mode]);

  const value: ThemeModeContextValue = {
    mode,
    isDark: mode === 'dark',
    toggleMode,
    setMode,
  };

  return (
    <ThemeModeContext.Provider value={value}>
      {children}
    </ThemeModeContext.Provider>
  );
}
