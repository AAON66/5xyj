import { Link } from 'react-router-dom';

import { useAggregateSession, useApiFeedback } from '../hooks';
import { cancelAggregateSession, clearAggregateSession } from '../services/aggregateSessionStore';

const TEXT = {
  aggregateRunningTitle: '快速聚合正在后台运行',
  aggregateView: '回到聚合页',
  aggregateCancel: '取消聚合',
  aggregateDoneTitle: '快速聚合记录已保留',
  aggregateClear: '清除记录',
  loadingTitle: '正在同步页面数据',
  loadingMessage: (count: number) => `当前有 ${count} 个请求处理中`,
  close: '关闭',
};

export function GlobalFeedback() {
  const { clearError, lastError, pendingRequests } = useApiFeedback();
  const aggregateSession = useAggregateSession();

  const aggregateMessage = aggregateSession.progress
    ? `${aggregateSession.progress.percent}% | ${aggregateSession.progress.label} | ${aggregateSession.progress.message}`
    : aggregateSession.error;

  return (
    <div className="feedback-stack" aria-live="polite">
      {aggregateSession.status === 'running' ? (
        <div className="feedback-banner feedback-banner--aggregate">
          <div>
            <strong>{TEXT.aggregateRunningTitle}</strong>
            <span>{aggregateMessage}</span>
          </div>
          <div className="feedback-banner__actions">
            <Link to="/" className="button button--ghost">
              {TEXT.aggregateView}
            </Link>
            <button type="button" onClick={cancelAggregateSession}>
              {TEXT.aggregateCancel}
            </button>
          </div>
        </div>
      ) : null}
      {aggregateSession.status !== 'idle' && aggregateSession.status !== 'running' && aggregateSession.progress ? (
        <div className="feedback-banner feedback-banner--info">
          <div>
            <strong>{TEXT.aggregateDoneTitle}</strong>
            <span>{aggregateMessage}</span>
          </div>
          <div className="feedback-banner__actions">
            <Link to="/" className="button button--ghost">
              {TEXT.aggregateView}
            </Link>
            <button type="button" onClick={clearAggregateSession}>
              {TEXT.aggregateClear}
            </button>
          </div>
        </div>
      ) : null}
      {pendingRequests > 0 ? (
        <div className="feedback-banner feedback-banner--loading">
          <div>
            <strong>{TEXT.loadingTitle}</strong>
            <span>{TEXT.loadingMessage(pendingRequests)}</span>
          </div>
        </div>
      ) : null}
      {lastError ? (
        <div className="feedback-banner feedback-banner--error" role="alert">
          <div>
            <strong>{lastError.code ?? 'request_error'}</strong>
            <span>{lastError.message}</span>
          </div>
          <button type="button" onClick={clearError}>
            {TEXT.close}
          </button>
        </div>
      ) : null}
    </div>
  );
}
