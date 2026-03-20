import { useEffect, useMemo, useState } from 'react';

import { PageContainer, SectionState, SurfaceNotice } from '../components';
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
      return '错误';
    case 'warning':
      return '警告';
    case 'info':
      return '提示';
    default:
      return value;
  }
}

function matchLabel(value: string): string {
  switch (value) {
    case 'matched':
      return '已匹配';
    case 'unmatched':
      return '未匹配';
    case 'duplicate':
      return '重复命中';
    case 'low_confidence':
      return '低置信度';
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
  const [panelNotice, setPanelNotice] = useState<{ tone: 'success' | 'warning'; message: string } | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadBatches() {
      try {
        const result = await fetchRuntimeBatches();
        if (!active) {
          return;
        }
        setBatches(result);
        setPageError(null);
        if (result[0]) {
          setSelectedBatchId(result[0].id);
        }
      } catch {
        if (active) {
          setPageError('运行结果页面暂时无法读取批次列表，请稍后重试。');
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
      try {
        const [validationData, matchData] = await Promise.all([
          fetchBatchValidation(batchId).catch(() => null),
          fetchBatchMatch(batchId).catch(() => null),
        ]);
        if (!active) {
          return;
        }
        setValidation(validationData);
        setMatchResult(matchData);
      } catch {
        if (active) {
          setPageError('当前批次的校验或匹配结果加载失败。');
        }
      }
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

  const validationIssues = useMemo<ValidationIssue[]>(() => validation?.source_files.flatMap((item) => item.issues) ?? [], [validation]);
  const matchRows = useMemo<MatchRecord[]>(() => matchResult?.source_files.flatMap((item) => item.results) ?? [], [matchResult]);

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
    setPanelNotice(null);
    try {
      const result = await validateBatch(selectedBatchId);
      setValidation(result);
      setPanelNotice({ tone: 'success', message: `${result.batch_name} 已完成校验。` });
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
    setPanelNotice(null);
    try {
      const result = await matchBatch(selectedBatchId);
      setMatchResult(result);
      setPanelNotice({ tone: result.blocked_reason ? 'warning' : 'success', message: result.blocked_reason ?? `${result.batch_name} 已完成工号匹配。` });
      await refreshBatches(selectedBatchId);
    } finally {
      setRunningMatch(false);
    }
  }

  return (
    <PageContainer
      eyebrow="Results"
      title="校验与匹配结果"
      description="按批次执行数据校验和工号匹配，并集中查看问题明细、候选工号和阻塞原因。"
      actions={
        <div className="button-row">
          <button type="button" className="button button--primary" onClick={() => void handleValidate()} disabled={!selectedBatchId || runningValidation}>
            {runningValidation ? '校验中...' : '执行数据校验'}
          </button>
          <button type="button" className="button button--ghost" onClick={() => void handleMatch()} disabled={!selectedBatchId || runningMatch}>
            {runningMatch ? '匹配中...' : '执行工号匹配'}
          </button>
        </div>
      }
    >
      {panelNotice ? <SurfaceNotice tone={panelNotice.tone} message={panelNotice.message} /> : null}
      {pageError ? <SurfaceNotice tone="error" title="页面状态异常" message={pageError} /> : null}

      <div className="panel-grid panel-grid--two runtime-layout">
        <section className="panel-card runtime-batch-list">
          <div>
            <span className="panel-label">批次选择</span>
            <strong>{loading ? '加载中...' : `${batches.length} 个可用批次`}</strong>
            <p>切换批次后，这里会展示该批次已经持久化的校验与匹配结果。</p>
          </div>
          {loading ? (
            <SectionState title="正在加载批次" message="系统正在同步运行结果页面需要的批次列表。" />
          ) : batches.length === 0 ? (
            <SectionState title="暂无可运行批次" message="先完成导入与解析，再回来执行校验和匹配。" />
          ) : (
            <div className="batch-list">
              {batches.map((batch) => (
                <button key={batch.id} type="button" className={`batch-card${selectedBatchId === batch.id ? ' is-active' : ''}`} onClick={() => setSelectedBatchId(batch.id)}>
                  <strong>{batch.batch_name}</strong>
                  <span>{batch.status}</span>
                  <small>{formatDateTime(batch.updated_at)}</small>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="panel-card runtime-summary-grid">
          <div className="summary-grid">
            <article className="status-item">
              <strong>{validation?.total_issue_count ?? 0}</strong>
              <div>校验问题</div>
            </article>
            <article className="status-item">
              <strong>{matchResult?.matched_count ?? 0}</strong>
              <div>已匹配</div>
            </article>
            <article className="status-item">
              <strong>{matchResult?.unmatched_count ?? 0}</strong>
              <div>未匹配</div>
            </article>
            <article className="status-item">
              <strong>{matchResult?.duplicate_count ?? 0}</strong>
              <div>重复命中</div>
            </article>
          </div>
          <div className="status-item">
            <strong>员工主档状态</strong>
            <div>
              {matchResult
                ? matchResult.employee_master_available
                  ? `当前可用员工主档 ${matchResult.employee_master_count} 条。`
                  : matchResult.blocked_reason ?? '员工主档暂不可用。'
                : '选择批次后，这里会显示匹配前置条件。'}
            </div>
          </div>
        </section>
      </div>

      <div className="panel-grid panel-grid--two runtime-detail-grid">
        <section className="panel-card">
          <div className="section-heading">
            <div>
              <span className="panel-label">校验问题</span>
              <h2>问题明细</h2>
            </div>
          </div>
          {validationIssues.length > 0 ? (
            <div className="issue-list">
              {validationIssues.map((issue) => (
                <article key={`${issue.normalized_record_id ?? 'none'}-${issue.source_row_number}-${issue.issue_type}`} className="issue-card">
                  <div className="issue-card__head">
                    <strong>第 {issue.source_row_number} 行</strong>
                    <span className={`severity-badge severity-badge--${issue.severity}`}>{severityLabel(issue.severity)}</span>
                  </div>
                  <div>{issue.message}</div>
                  <small>
                    类型 {issue.issue_type}
                    {issue.field_name ? ` · 字段 ${issue.field_name}` : ''}
                  </small>
                </article>
              ))}
            </div>
          ) : (
            <SectionState title="暂无校验问题" message="执行校验后，如果发现缺失、格式或金额问题，这里会展示详细结果。" />
          )}
        </section>

        <section className="panel-card">
          <div className="section-heading">
            <div>
              <span className="panel-label">匹配结果</span>
              <h2>工号命中明细</h2>
            </div>
          </div>
          {matchRows.length > 0 ? (
            <div className="match-list">
              {matchRows.map((item) => (
                <article key={`${item.normalized_record_id ?? 'none'}-${item.source_row_number}`} className="match-card">
                  <div className="match-card__head">
                    <strong>{item.person_name ?? '未识别姓名'}</strong>
                    <span className={`match-badge match-badge--${item.match_status}`}>{matchLabel(item.match_status)}</span>
                  </div>
                  <div>源数据第 {item.source_row_number} 行</div>
                  <div>证件号：{item.id_number ?? '-'}</div>
                  <div>工号：{item.employee_id ?? '-'}</div>
                  <small>
                    {item.match_basis ? `依据 ${item.match_basis}` : '尚未命中匹配依据'}
                    {item.confidence !== null ? ` · 置信度 ${item.confidence.toFixed(2)}` : ''}
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
            <SectionState title="暂无匹配结果" message="执行工号匹配后，这里会展示命中、未命中和低置信度候选。" />
          )}
        </section>
      </div>
    </PageContainer>
  );
}
