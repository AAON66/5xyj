import { ApiClientError, normalizeApiError } from './api';
import {
  runSimpleAggregateWithProgress,
  type AggregateInput,
  type AggregateProgressEvent,
  type AggregateRunResult,
} from './aggregate';

export type AggregateSessionStatus = 'idle' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface AggregateSelectionSummary {
  socialFiles: string[];
  housingFundFiles: string[];
  employeeMasterFile: string | null;
  batchName: string;
}

export interface AggregateSessionSnapshot {
  status: AggregateSessionStatus;
  selection: AggregateSelectionSummary;
  progress: AggregateProgressEvent | null;
  result: AggregateRunResult | null;
  error: string | null;
  startedAt: string | null;
  finishedAt: string | null;
}

const STORAGE_KEY = 'simple_aggregate_session_snapshot_v1';
const CANCELLED_MESSAGE = '已取消当前聚合任务。';
const INTERRUPTED_MESSAGE = '页面刷新后无法继续原有聚合任务，请重新发起。';

const listeners = new Set<() => void>();
let currentController: AbortController | null = null;
let currentTask: Promise<AggregateRunResult> | null = null;
let snapshot: AggregateSessionSnapshot = restoreSnapshot();

function emptySelection(): AggregateSelectionSummary {
  return {
    socialFiles: [],
    housingFundFiles: [],
    employeeMasterFile: null,
    batchName: '',
  };
}

function emptySnapshot(): AggregateSessionSnapshot {
  return {
    status: 'idle',
    selection: emptySelection(),
    progress: null,
    result: null,
    error: null,
    startedAt: null,
    finishedAt: null,
  };
}

function restoreSnapshot(): AggregateSessionSnapshot {
  if (typeof window === 'undefined') {
    return emptySnapshot();
  }

  const raw = window.sessionStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return emptySnapshot();
  }

  try {
    const parsed = JSON.parse(raw) as AggregateSessionSnapshot;
    if (parsed.status === 'running') {
      return {
        ...parsed,
        status: 'cancelled',
        error: INTERRUPTED_MESSAGE,
        finishedAt: new Date().toISOString(),
      };
    }
    return parsed;
  } catch {
    return emptySnapshot();
  }
}

function persistSnapshot(): void {
  if (typeof window === 'undefined') {
    return;
  }
  window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
}

function emitChange(): void {
  persistSnapshot();
  listeners.forEach((listener) => listener());
}

function setSnapshot(next: AggregateSessionSnapshot): void {
  snapshot = next;
  emitChange();
}

function patchSnapshot(patch: Partial<AggregateSessionSnapshot>): void {
  setSnapshot({ ...snapshot, ...patch });
}

function summarizeSelection(input: AggregateInput): AggregateSelectionSummary {
  return {
    socialFiles: input.files.map((file) => file.name),
    housingFundFiles: (input.housingFundFiles ?? []).map((file) => file.name),
    employeeMasterFile: input.employeeMasterFile?.name ?? null,
    batchName: input.batchName?.trim() ?? '',
  };
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError';
}

export function subscribeToAggregateSession(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function getAggregateSessionSnapshot(): AggregateSessionSnapshot {
  return snapshot;
}

export function startAggregateSession(input: AggregateInput): Promise<AggregateRunResult> {
  if (currentTask) {
    throw new ApiClientError('已有聚合任务正在进行，请先等待或主动取消。');
  }

  currentController = new AbortController();
  setSnapshot({
    status: 'running',
    selection: summarizeSelection(input),
    progress: {
      stage: 'employee_import',
      label: '准备开始',
      message: '正在初始化快速聚合任务。',
      percent: 0,
    },
    result: null,
    error: null,
    startedAt: new Date().toISOString(),
    finishedAt: null,
  });

  currentTask = runSimpleAggregateWithProgress({
    ...input,
    signal: currentController.signal,
    onProgress: (progress) => {
      patchSnapshot({ progress });
    },
  })
    .then((result) => {
      setSnapshot({
        ...snapshot,
        status: 'completed',
        result,
        progress:
          snapshot.progress ?? {
            stage: 'export',
            label: '导出完成',
            message: '双模板聚合任务已结束。',
            percent: 100,
            batch_id: result.batch_id,
            batch_name: result.batch_name,
          },
        error: null,
        finishedAt: new Date().toISOString(),
      });
      return result;
    })
    .catch((error: unknown) => {
      if (isAbortError(error) || currentController?.signal.aborted) {
        setSnapshot({
          ...snapshot,
          status: 'cancelled',
          error: CANCELLED_MESSAGE,
          finishedAt: new Date().toISOString(),
        });
        throw new ApiClientError(CANCELLED_MESSAGE);
      }

      const normalized = normalizeApiError(error);
      setSnapshot({
        ...snapshot,
        status: 'failed',
        error: normalized.message,
        finishedAt: new Date().toISOString(),
      });
      throw normalized;
    })
    .finally(() => {
      currentController = null;
      currentTask = null;
    });

  return currentTask;
}

export function cancelAggregateSession(): void {
  currentController?.abort();
}

export function clearAggregateSession(): void {
  if (currentController) {
    currentController.abort();
  }
  currentController = null;
  currentTask = null;
  setSnapshot(emptySnapshot());
}
