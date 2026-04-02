import { useEffect, useState } from 'react';

import { fetchFeatureFlags, type FeatureFlags } from '../services/feishu';

const DEFAULT_FLAGS: FeatureFlags = {
  feishu_sync_enabled: false,
  feishu_oauth_enabled: false,
  feishu_credentials_configured: false,
};

export function useFeishuFeatureFlag() {
  const [flags, setFlags] = useState<FeatureFlags>(DEFAULT_FLAGS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFeatureFlags()
      .then(setFlags)
      .catch(() => setFlags(DEFAULT_FLAGS))
      .finally(() => setLoading(false));
  }, []);

  return { ...flags, loading };
}
