import { useCallback, useEffect, useState } from 'react';

import { fetchFeatureFlags, type FeatureFlags } from '../services/feishu';

const DEFAULT_FLAGS: FeatureFlags = {
  feishu_sync_enabled: false,
  feishu_oauth_enabled: false,
  feishu_credentials_configured: false,
};

export function useFeishuFeatureFlag() {
  const [flags, setFlags] = useState<FeatureFlags>(DEFAULT_FLAGS);
  const [loading, setLoading] = useState(true);

  const refreshFlags = useCallback(async () => {
    setLoading(true);
    try {
      setFlags(await fetchFeatureFlags());
    } catch {
      setFlags(DEFAULT_FLAGS);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshFlags();
  }, [refreshFlags]);

  return { ...flags, loading, refreshFlags };
}
