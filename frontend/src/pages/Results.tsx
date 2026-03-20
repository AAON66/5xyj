import { useEffect, useMemo, useState } from 'react';

import { PageContainer } from '../components';
import {
  fetchBatchMatch,
  fetchBatchValidation,
  fetchRuntimeBatches,
  matchBatch,
  type BatchMatch,
  type BatchValidation,
  type MatchRecord,
  type ValidationIssue,
  validateBatch,
} from '../services/runtime';

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

function severityLabel(value: string): string {
  switch (value) {
    case 'error':
      return '??';
    case 'warning':
      return '??';
    case 'info':
      return '??';
    default:
      return value;
  }
}

function matchLabel(value: string): string {
  switch (value) {
    case 'matched':
      return '???';
    case 'unmatched':
      return '???';
    case 'duplicate':
      return '????';
    case 'low_confidence':
      return '????';
    default:
      return value;
  }
}

export function ResultsPage() {
  const [batches, setBatches] = useState<Array<{ id: string; batch_name: string; status: string; updated_at: string }>>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
  const [validation, setValidation] = useState<BatchValidation | null>(null);
  const [matchResult, setMatchResult] = useState<BatchMatch | null>(null);
  const [loading, setLoading] = useState(true);
  const [runningValidation, setRunningValidation] = useState(false);
  const [runningMatch, setRunningMatch] = useState(false);
  const [panelMessage, setPanelMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadBatches() {
      try {
        const result = await fetchRuntimeBatches();
        if (!active) {
          return;
        }
        setBatches(result);
        if (result[0]) {
          setSelectedBatchId(result[0].id);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadBatches();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function loadRuntimeState(batchId: string) {
      const [validationData, matchData] = await Promise.all([
        fetchBatchValidation(batchId).catch(() => null),
        fetchBatchMatch(batchId).catch(() => null),
      ]);
      if (!active) {
        return;
      }
      setValidation(validationData);
      setMatchResult(matchData);
    }

    if (!selectedBatchId) {
      setValidation(null);
      setMatchResult(null);
      return;
    }

    void loadRuntimeState(selectedBatchId);
    return () => {
      active = false;
    };
  }, [selectedBatchId]);

  const validationIssues = useMemo<ValidationIssue[]>(() => {
    return validation?.source_files.flatMap((item) => item.issues) ?? [];
  }, [validation]);

  const matchRows = useMemo<MatchRecord[]>(() => {
    return matchResult?.source_files.flatMap((item) => item.results) ?? [];
  }, [matchResult]);

  async function refreshBatches(keepId?: string) {
    const result = await fetchRuntimeBatches();
    setBatches(result);
    if (keepId) {
      setSelectedBatchId(keepId);
    }
  }

  async function handleValidate() {
    if (!selectedBatchId) {
      return;
    }
    setRunningValidation(true);
    setPanelMessage(null);
    try {
      const result = await validateBatch(selectedBatchId);
      setValidation(result);
      setPanelMessage(`?? ${result.batch_name} ?????????`);
      await refreshBatches(selectedBatchId);
    } finally {
      setRunningValidation(false);
    }
  }

  async function handleMatch() {
    if (!selectedBatchId) {
      return;
    }
    setRunningMatch(true);
    setPanelMessage(null);
    try {
      const result = await matchBatch(selectedBatchId);
      setMatchResult(result);
      setPanelMessage(result.blocked_reason ?? `?? ${result.batch_name} ?????????`);
      await refreshBatches(selectedBatchId);
    } finally {
      setRunningMatch(false);
    }
  }

  return (
    <PageContainer
      eyebrow="Results"
      title="???????"
      description="????????????????????????????????????????"
      actions={
        <div className="button-row">
          <button type="button" className="button button--primary" onClick={() => void handleValidate()} disabled={!selectedBatchId || runningValidation}>
            {runningValidation ? '???...' : '??????'}
          </button>
          <button type="button" className="button button--ghost" onClick={() => void handleMatch()} disabled={!selectedBatchId || runningMatch}>
            {runningMatch ? '???...' : '??????'}
          </button>
        </div>
      }
    >
      <div className="panel-grid panel-grid--two runtime-layout">
        <section className="panel-card runtime-batch-list">
          <div>
            <span className="panel-label">????</span>
            <strong>{loading ? '???...' : `${batches.length} ??????`}</strong>
            <p>??????????????????????????????????</p>
          </div>
          <div className="batch-list">
            {batches.length === 0 ? (
              <div className="status-item">?????????????????????????</div>
            ) : (
              batches.map((batch) => (
                <button
                  key={batch.id}
                  type="button"
                  className={`batch-card${selectedBatchId === batch.id ? ' is-active' : ''}`}
                  onClick={() => setSelectedBatchId(batch.id)}
                >
                  <strong>{batch.batch_name}</strong>
                  <span>{batch.status}</span>
                  <small>{formatDateTime(batch.updated_at)}</small>
                </button>
              ))
            )}
          </div>
          {panelMessage ? <div className="inline-status inline-status--success">{panelMessage}</div> : null}
        </section>

        <section className="panel-card runtime-summary-grid">
          <div className="summary-grid">
            <article className="status-item">
              <strong>{validation?.total_issue_count ?? 0}</strong>
              <div>????</div>
            </article>
            <article className="status-item">
              <strong>{matchResult?.matched_count ?? 0}</strong>
              <div>???</div>
            </article>
            <article className="status-item">
              <strong>{matchResult?.unmatched_count ?? 0}</strong>
              <div>???</div>
            </article>
            <article className="status-item">
              <strong>{matchResult?.duplicate_count ?? 0}</strong>
              <div>????</div>
            </article>
          </div>
          <div className="status-item">
            <strong>????</strong>
            <div>
              {matchResult
                ? matchResult.employee_master_available
                  ? `???????? ${matchResult.employee_master_count} ??????`
                  : matchResult.blocked_reason ?? '????????'
                : '???????????????'}
            </div>
          </div>
        </section>
      </div>

      <div className="panel-grid panel-grid--two runtime-detail-grid">
        <section className="panel-card">
          <div className="section-heading">
            <div>
              <span className="panel-label">????</span>
              <h2>??????</h2>
            </div>
          </div>
          {validationIssues.length > 0 ? (
            <div className="issue-list">
              {validationIssues.map((issue) => (
                <article key={`${issue.normalized_record_id ?? 'none'}-${issue.source_row_number}-${issue.issue_type}`} className="issue-card">
                  <div className="issue-card__head">
                    <strong>? {issue.source_row_number} ?</strong>
                    <span className={`severity-badge severity-badge--${issue.severity}`}>{severityLabel(issue.severity)}</span>
                  </div>
                  <div>{issue.message}</div>
                  <small>
                    ?? {issue.issue_type}
                    {issue.field_name ? ` ? ?? ${issue.field_name}` : ''}
                  </small>
                </article>
              ))}
            </div>
          ) : (
            <div className="status-item">????????????????????????????</div>
          )}
        </section>

        <section className="panel-card">
          <div className="section-heading">
            <div>
              <span className="panel-label">????</span>
              <h2>??????</h2>
            </div>
          </div>
          {matchRows.length > 0 ? (
            <div className="match-list">
              {matchRows.map((item) => (
                <article key={`${item.normalized_record_id ?? 'none'}-${item.source_row_number}`} className="match-card">
                  <div className="match-card__head">
                    <strong>{item.person_name ?? '?????'}</strong>
                    <span className={`match-badge match-badge--${item.match_status}`}>{matchLabel(item.match_status)}</span>
                  </div>
                  <div>????? {item.source_row_number} ?</div>
                  <div>????{item.id_number ?? '?'}</div>
                  <div>???{item.employee_id ?? '?'}</div>
                  <small>
                    {item.match_basis ? `?? ${item.match_basis}` : '??????'}
                    {item.confidence !== null ? ` ? ??? ${item.confidence.toFixed(2)}` : ''}
                  </small>
                  {item.candidate_employee_ids.length > 0 ? (
                    <div className="candidate-chip-list">
                      {item.candidate_employee_ids.map((candidate) => (
                        <span key={candidate} className="file-chip">
                          {candidate}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </article>
              ))}
            </div>
          ) : (
            <div className="status-item">????????????????????????????</div>
          )}
        </section>
      </div>
    </PageContainer>
  );
}
