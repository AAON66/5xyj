import { useState, useCallback } from 'react';

const STORAGE_KEY = 'menu-open-keys';

export function useMenuOpenKeys(defaultKeys: string[], validKeys: string[]) {
  const [openKeys, setOpenKeys] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          const cleaned = parsed.filter(
            (k: unknown) => typeof k === 'string' && validKeys.includes(k)
          );
          return cleaned.length > 0 ? cleaned : defaultKeys;
        }
      }
    } catch {
      /* fallback to default — covers JSON parse error, Safari private mode, SSR */
    }
    return defaultKeys;
  });

  const onOpenChange = useCallback((keys: string[]) => {
    setOpenKeys(keys);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(keys));
    } catch {
      /* Safari private mode or quota exceeded */
    }
  }, []);

  return { openKeys, onOpenChange };
}
