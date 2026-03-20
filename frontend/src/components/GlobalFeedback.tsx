import { useApiFeedback } from '../hooks';

export function GlobalFeedback() {
  const { clearError, lastError, pendingRequests } = useApiFeedback();

  return (
    <div className="feedback-stack" aria-live="polite">
      {pendingRequests > 0 ? (
        <div className="feedback-banner feedback-banner--loading">
          <strong>正在同步后端状态</strong>
          <span>{pendingRequests} 个请求处理中</span>
        </div>
      ) : null}
      {lastError ? (
        <div className="feedback-banner feedback-banner--error" role="alert">
          <div>
            <strong>{lastError.code ?? 'request_error'}</strong>
            <span>{lastError.message}</span>
          </div>
          <button type="button" onClick={clearError}>
            关闭
          </button>
        </div>
      ) : null}
    </div>
  );
}
