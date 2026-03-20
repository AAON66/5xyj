import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { PageContainer } from '../components';
import {
  fetchImportBatch,
  fetchImportBatchPreview,
  parseImportBatch,
  type HeaderMappingPreview,
  type ImportBatchDetail,
  type ImportBatchPreview,
  type SourceFilePreview,
} from '../services/imports';

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

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === '') {
    return '-';
  }
  if (typeof value === 'object') {
    return JSON.stringify(value);
  }
  return String(value);
}

function summarizeMapping(mapping: HeaderMappingPreview): string {
  if (mapping.canonical_field) {
    return mapping.canonical_field;
  }
  if (mapping.candidate_fields.length > 0) {
    return `候选: ${mapping.candidate_fields.join(', ')}`;
  }
  return '未识别';
}

export function ImportBatchDetailPage() {
  const { batchId } = useParams<{ batchId: string }>();
  const [batchDetail, setBatchDetail] = useState<ImportBatchDetail | null>(null);
  const [preview, setPreview] = useState<ImportBatchPreview | null>(null);
  const [selectedSourceFileId, setSelectedSourceFileId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [parsing, setParsing] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [panelMessage, setPanelMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadBatch() {
      if (!batchId) {
        setLoading(false);
        return;
      }

      try {
        const [detailResult, previewResult] = await Promise.all([
          fetchImportBatch(batchId),
          fetchImportBatchPreview(batchId).catch(() => null),
        ]);
        if (!active) {
          return;
        }
        setBatchDetail(detailResult);
        setPreview(previewResult);
        const firstSourceFileId = previewResult?.source_files[0]?.source_file_id ?? detailResult.source_files[0]?.id ?? null;
        setSelectedSourceFileId((current) => current ?? firstSourceFileId);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadBatch();
    return () => {
      active = false;
    };
  }, [batchId]);

  const selectedSourceFile = useMemo<SourceFilePreview | null>(() => {
    if (!preview?.source_files.length) {
      return null;
    }
    return preview.source_files.find((item) => item.source_file_id === selectedSourceFileId) ?? preview.source_files[0] ?? null;
  }, [preview, selectedSourceFileId]);

  const previewColumns = useMemo(() => {
    const firstRecord = selectedSourceFile?.preview_records[0];
    return firstRecord ? Object.keys(firstRecord.values) : [];
  }, [selectedSourceFile]);

  async function reloadBatchState(targetBatchId: string) {
    setRefreshing(true);
    try {
      const [detailResult, previewResult] = await Promise.all([
        fetchImportBatch(targetBatchId),
        fetchImportBatchPreview(targetBatchId).catch(() => null),
      ]);
      setBatchDetail(detailResult);
      setPreview(previewResult);
      const firstSourceFileId = previewResult?.source_files[0]?.source_file_id ?? detailResult.source_files[0]?.id ?? null;
      setSelectedSourceFileId((current) => current ?? firstSourceFileId);
    } finally {
      setRefreshing(false);
    }
  }

  async function handleParseBatch() {
    if (!batchId) {
      return;
    }
    setParsing(true);
    setPanelMessage(null);
    try {
      const parsed = await parseImportBatch(batchId);
      setPreview(parsed);
      setSelectedSourceFileId(parsed.source_files[0]?.source_file_id ?? null);
      await reloadBatchState(batchId);
      setPanelMessage('批次解析已刷新，下面是最新预览结果。');
    } finally {
      setParsing(false);
    }
  }

  return (
    <PageContainer
      eyebrow="Batch Detail"
      title={batchDetail ? batchDetail.batch_name : '导入批次详情'}
      description="按批次查看源文件、解析预览、表头映射、过滤行和标准化样本，为后续校验、匹配和人工修正提供统一入口。"
      actions={
        <div className="button-row">
          <Link to="/imports" className="button button--ghost">
            返回批次列表
          </Link>
          <button type="button" className="button button--primary" onClick={() => void handleParseBatch()} disabled={!batchId || parsing}>
            {parsing ? '刷新解析中...' : '刷新解析结果'}
          </button>
        </div>
      }
    >
      <div className="panel-grid panel-grid--two batch-detail-hero-grid">
        <section className="panel-card panel-card--soft">
          <span className="panel-label">批次概况</span>
          <strong>{loading ? '加载中...' : batchDetail?.batch_name ?? '未找到批次'}</strong>
          <p>
            {batchDetail
              ? `${batchDetail.file_count} 个文件，当前状态为 ${batchDetail.status}，创建于 ${formatDateTime(batchDetail.created_at)}。`
              : '如果这里没有加载到批次，说明该批次还不存在或接口暂时不可用。'}
          </p>
          <div className="batch-detail-meta-grid">
            <div>
              <span>最后更新时间</span>
              <strong>{batchDetail ? formatDateTime(batchDetail.updated_at) : '-'}</strong>
            </div>
            <div>
              <span>预览文件数</span>
              <strong>{preview?.source_files.length ?? 0}</strong>
            </div>
          </div>
        </section>

        <section className="panel-card panel-card--soft">
          <span className="panel-label">详情说明</span>
          <strong>先看文件，再看表头与样本</strong>
          <p>这个页面按单个批次聚合了上传文件、命中 sheet、表头签名、过滤行和标准化前 20 行，方便我们快速判断解析质量。</p>
          {panelMessage ? <div className="inline-status inline-status--success">{panelMessage}</div> : null}
          {refreshing ? <div className="inline-status inline-status--success">正在刷新批次详情...</div> : null}
        </section>
      </div>

      <section className="panel-card">
        <div className="section-heading">
          <div>
            <span className="panel-label">源文件</span>
            <h2>批次内文件列表</h2>
          </div>
        </div>
        {batchDetail?.source_files.length ? (
          <div className="source-file-summary-grid">
            {batchDetail.source_files.map((file) => {
              const isActive = selectedSourceFile?.source_file_id === file.id;
              return (
                <button
                  key={file.id}
                  type="button"
                  className={`source-file-summary-card${isActive ? ' is-active' : ''}`}
                  onClick={() => setSelectedSourceFileId(file.id)}
                >
                  <strong>{file.file_name}</strong>
                  <span>{file.region ?? '自动识别地区'}</span>
                  <small>{file.company_name ?? '未提供公司名'}</small>
                  <small>{Math.max(1, Math.round(file.file_size / 1024))} KB</small>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="status-item">当前批次还没有源文件。</div>
        )}
      </section>

      <div className="panel-grid panel-grid--two import-summary-grid">
        <article className="panel-card panel-card--soft">
          <span className="panel-label">命中工作表</span>
          <strong>{selectedSourceFile ? selectedSourceFile.raw_sheet_name : '尚未解析'}</strong>
          <p>
            {selectedSourceFile
              ? `${selectedSourceFile.normalized_record_count} 条标准化记录，过滤 ${selectedSourceFile.filtered_row_count} 条非明细行。`
              : '运行解析后，这里会显示当前文件命中的工作表和记录规模。'}
          </p>
        </article>
        <article className="panel-card panel-card--soft">
          <span className="panel-label">表头签名</span>
          <strong>{selectedSourceFile ? selectedSourceFile.raw_header_signature : '尚未生成'}</strong>
          <p>{selectedSourceFile ? '这段签名可用于追踪规则命中和后续人工修正。' : '解析完成后，这里会展示表头展开后的签名。'}</p>
        </article>
      </div>

      <div className="panel-grid panel-grid--two import-detail-grid">
        <section className="panel-card">
          <div className="section-heading">
            <div>
              <span className="panel-label">映射结果</span>
              <h2>表头识别与规则归一化</h2>
            </div>
          </div>
          {selectedSourceFile?.header_mappings.length ? (
            <div className="mapping-list">
              {selectedSourceFile.header_mappings.map((mapping) => (
                <article key={mapping.raw_header_signature} className="mapping-card">
                  <div className="mapping-card__head">
                    <strong>{mapping.raw_header}</strong>
                    <span className={`mapping-badge${mapping.canonical_field ? '' : ' mapping-badge--warn'}`}>
                      {summarizeMapping(mapping)}
                    </span>
                  </div>
                  <p>{mapping.raw_header_signature}</p>
                  <small>
                    来源 {mapping.mapping_source}
                    {mapping.confidence !== null ? ` · 置信度 ${mapping.confidence.toFixed(2)}` : ''}
                    {mapping.llm_attempted ? ` · LLM ${mapping.llm_status}` : ''}
                  </small>
                </article>
              ))}
            </div>
          ) : (
            <div className="status-item">当前文件还没有映射结果。先执行解析后再查看。</div>
          )}
        </section>

        <section className="panel-card">
          <div className="section-heading">
            <div>
              <span className="panel-label">过滤结果</span>
              <h2>非明细行</h2>
            </div>
          </div>
          {selectedSourceFile?.filtered_rows.length ? (
            <div className="filtered-list">
              {selectedSourceFile.filtered_rows.map((row) => (
                <div key={`${row.row_number}-${row.reason}`} className="filtered-row-card">
                  <strong>第 {row.row_number} 行</strong>
                  <span>{row.reason}</span>
                  <small>{row.first_value}</small>
                </div>
              ))}
            </div>
          ) : (
            <div className="status-item">当前文件没有检测到被过滤的非明细行。</div>
          )}
        </section>
      </div>

      <section className="panel-card">
        <div className="section-heading">
          <div>
            <span className="panel-label">标准化预览</span>
            <h2>前 20 行标准字段样本</h2>
          </div>
        </div>
        {selectedSourceFile?.preview_records.length ? (
          <div className="preview-table-wrap">
            <table className="preview-table">
              <thead>
                <tr>
                  <th>源行号</th>
                  {previewColumns.map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {selectedSourceFile.preview_records.map((record) => (
                  <tr key={record.source_row_number}>
                    <td>{record.source_row_number}</td>
                    {previewColumns.map((column) => (
                      <td key={`${record.source_row_number}-${column}`}>{formatValue(record.values[column])}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="status-item">当前批次还没有标准化预览，先刷新解析结果后再查看。</div>
        )}
      </section>

      <section className="panel-card">
        <div className="section-heading">
          <div>
            <span className="panel-label">未识别字段</span>
            <h2>待后续映射或人工修正</h2>
          </div>
        </div>
        {selectedSourceFile?.preview_records.some((record) => Object.keys(record.unmapped_values).length > 0) ? (
          <div className="unmapped-grid">
            {selectedSourceFile.preview_records
              .filter((record) => Object.keys(record.unmapped_values).length > 0)
              .slice(0, 6)
              .map((record) => (
                <article key={`unmapped-${record.source_row_number}`} className="status-item">
                  <strong>第 {record.source_row_number} 行</strong>
                  <div>
                    {Object.entries(record.unmapped_values).map(([key, value]) => (
                      <div key={key}>
                        {key}: {formatValue(value)}
                      </div>
                    ))}
                  </div>
                </article>
              ))}
          </div>
        ) : (
          <div className="status-item">当前预览中没有残留未识别字段。</div>
        )}
      </section>
    </PageContainer>
  );
}
