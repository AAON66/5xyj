import { useSyncExternalStore } from 'react';

import { getAggregateSessionSnapshot, subscribeToAggregateSession } from '../services/aggregateSessionStore';

export function useAggregateSession() {
  return useSyncExternalStore(
    subscribeToAggregateSession,
    getAggregateSessionSnapshot,
    getAggregateSessionSnapshot,
  );
}
