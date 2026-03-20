import { useEffect, useMemo, useState } from 'react';

import { PageContainer, SectionState, SurfaceNotice } from '../components';
import {
  exportBatch,
  fetchBatchExport,
  fetchRuntimeBatches,
  type BatchExport,
  type ExportArtifact,
} from '../services/runtime';

const TEMPLATE_ORDER = ['salary', 'final_tool'];

function formatDateTime(value: string | null): string {
  if (!value) {
    return '未完成';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

function exportStatusLabel(value: string | null): string {
  switch (value) {
    case 'completed':
      return '已完成';
    case 'failed':
      return '失败';
    case 'blocked':
      return '已阻塞';
    case 'running':
      return '导出中';
    case 'pending':
      return '待执行';
    default:
      return value ?? '未开始';
  }
}

function artifactStatusLabel(value: string): string {
  switch (value) {
    case 'completed':
      return '已导出';
    case 'failed':
      return '导出失败';
    case 'blocked':
      return '未满足条件';
    case 'missing_template':
      return '模板缺失';
    case 'pending':
      return '待生成';
    default:
      return value;
  }
}

function artifactStatusClass(value: string): string {
  switch (value) {
    case 'completed':
      return 'export-badge--completed';
    case 'failed':
      return 'export-badge--failed';
    case 'blocked':
    case 'missing_template':
      return 'export-badge--warn';
    default:
      return 'export-badge--pending';
  }
}

function templateLabel(value: string): string {
  switch (value) {
    case 'salary':
      return '薪酬模板';
    case 'final_tool':
      return '工具表最终版';
    default:
      return value;
  }
}

function sortArtifacts(artifacts: ExportArtifact[]): ExportArtifact[] {
  return [...artifacts].sort((left, right) => {
    const leftIndex = TEMPLATE_ORDER.indexOf(left.template_type);
    const rightIndex = TEMPLATE_ORDER.indexOf(right.template_type);
    return (leftIndex === -1 ? Number.MAX_SAFE_INTEGER : leftIndex) - (rightIndex === -1 ? Number.MAX_SAFE_INTEGER : rightIndex);
  });
}

export function ExportsPage() {
  const [batches, setBatches] = useState<Array<{ id: string; batch_name: string; status: string; updated_at: string }>>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
  const [exportResult, setExportResult] = useState<BatchExport | null>(null);
  const [loading, setLoading] = useState(true);
  const [runningExport, setRunningExport] = useState(false);
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
          setSelectedBatchId((current) => current ?? result[0].id);
        }
      } catch {
        if (active) {
          setPageError('导出页面暂时无法读取批次列表。');
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

    async function loadExportState(batchId: string) {
      try {
        const exportData = await fetchBatchExport(batchId).catch(() => null);
        if (!active) {
          return;
        }
        setExportResult(exportData);
      } catch {
        if (active) {
          setPageError('当前批次的导出快照加载失败。');
        }
      }
    }

    if (!selectedBatchId) {
      setExportResult(null);
      return;
    }

    void loadExportState(selectedBatchId);
    return () => {
      active = false;
    };
  }, [selectedBatchId]);

  const artifacts = useMemo<ExportArtifact[]>(() => sortArtifacts(exportResult?.artifacts ?? []), [exportResult]);

  async function refreshBatches(keepId?: string) {
    const result = await fetchRuntimeBatches();
    setBatches(result);
    if (keepId) {
      setSelectedBatchId(keepId);
    }
  }

  async function handleExport() {
    if (!selectedBatchId) {
      return;
    }

    setRunningExport(true);
    setPanelNotice(null);
    try {
      const result = await exportBatch(selectedBatchId);
      setExportResult(result);
      setPanelNotice({ tone: result.blocked_reason ? 'warning' : 'success', message: result.blocked_reason ?? `${result.batch_name} 的双模板导出已执行。` });
      await refreshBatches(selectedBatchId);
    } finally {
      setRunningExport(false);
    }
  }

  return (
    <PageContainer
      eyebrow="Exports"
      title="双模板导出"
      description="按批次触发薪酬模板和工具表最终版模板导出，并展示阻塞原因、模板状态、生成路径与完成时间。"
      actions={
        <div className="button-row">
          <button type="button" className="button button--primary" onClick={() => void handleExport()} disabled={!selectedBatchId || runningExport}>
            {runningExport ? '导出中...' : '执行双模板导出'}
          </button>
        </div>
      }
    >
      {panelNotice ? <SurfaceNotice tone={panelNotice.tone} message={panelNotice.message} /> : null}
      {pageError ? <SurfaceNotice tone="error" title="页面状态异常" message={pageError} /> : null}

      <div className="panel-grid panel-grid--two export-layout">
        <section className="panel-card export-batch-list">
          <div>
            <span className="panel-label">批次选择</span>
            <strong>{loading ? '加载中...' : `${batches.length} 个可用批次`}</strong>
            <p>选择已完成解析、校验和匹配的批次，查看最新导出快照或重新触发双模板导出。</p>
          </div>
          {loading ? (
            <SectionState title="正在加载批次" message="系统正在同步可执行导出的批次列表。" />
          ) : batches.length === 0 ? (
            <SectionState title="暂无可导出批次" message="先完成导入、解析和匹配，再回来执行双模板导出。" />
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

        <section className="panel-card export-summary-grid">
          <div className="summary-grid">
            <article className="status-item">
              <strong>{exportStatusLabel(exportResult?.export_status ?? exportResult?.status ?? null)}</strong>
              <div>当前导出状态</div>
            </article>
            <article className="status-item">
              <strong>{artifacts.length}</strong>
              <div>模板产物数</div>
            </article>
            <article className="status-item">
              <strong>{artifacts.filter((item) => item.status === 'completed').length}</strong>
              <div>成功模板数</div>
            </article>
            <article className="status-item">
              <strong>{artifacts.reduce((sum, item) => sum + item.row_count, 0)}</strong>
              <div>累计导出行数</div>
            </article>
          </div>
          <div className="status-item">
            <strong>运行说明</strong>
            <div>{exportResult?.blocked_reason ?? '系统会同时检查两份模板，只要任意一份失败，整体状态就会标记为失败。'}</div>
          </div>
          <div className="status-item">
            <strong>完成时间</strong>
            <div>{formatDateTime(exportResult?.completed_at ?? null)}</div>
          </div>
        </section>
      </div>

      <section className="panel-card">
        <div className="section-heading">
          <div>
            <span className="panel-label">模板产物</span>
            <h2>双模板执行结果</h2>
          </div>
        </div>
        {artifacts.length > 0 ? (
          <div className="artifact-grid">
            {artifacts.map((artifact) => (
              <article key={artifact.template_type} className="artifact-card">
                <div className="artifact-card__head">
                  <div>
                    <strong>{templateLabel(artifact.template_type)}</strong>
                    <p>{artifact.template_type}</p>
                  </div>
                  <span className={`export-badge ${artifactStatusClass(artifact.status)}`}>{artifactStatusLabel(artifact.status)}</span>
                </div>
                <div className="artifact-metadata">
                  <div>
                    <span>导出行数</span>
                    <strong>{artifact.row_count}</strong>
                  </div>
                  <div>
                    <span>文件路径</span>
                    <strong>{artifact.file_path ?? '尚未生成'}</strong>
                  </div>
                </div>
                {artifact.error_message ? <SurfaceNotice tone="warning" message={artifact.error_message} /> : null}
              </article>
            ))}
          </div>
        ) : (
          <SectionState title="暂无导出记录" message="当前批次还没有导出记录。完成匹配后即可在这里触发双模板导出。" />
        )}
      </section>
    </PageContainer>
  );
}
