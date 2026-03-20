import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { PageContainer } from '../components';
import {
  createImportBatch,
  fetchImportBatches,
  fetchImportBatch,
  fetchImportBatchPreview,
  parseImportBatch,
  type HeaderMappingPreview,
  type ImportBatchDetail,
  type ImportBatchPreview,
  type ImportBatchSummary,
  type SourceFilePreview,
} from '../services/imports';

const PRESET_REGIONS = [
  { value: '', label: '自动识别 / 不指定' },
  { value: 'guangzhou', label: '广州' },
  { value: 'hangzhou', label: '杭州' },
  { value: 'xiamen', label: '厦门' },
  { value: 'shenzhen', label: '深圳' },
  { value: 'wuhan', label: '武汉' },
  { value: 'changsha', label: '长沙' },
];

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

export function ImportsPage() {
  const [batches, setBatches] = useState<ImportBatchSummary[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
  const [selectedBatch, setSelectedBatch] = useState<ImportBatchDetail | null>(null);
  const [preview, setPreview] = useState<ImportBatchPreview | null>(null);
  const [batchName, setBatchName] = useState('');
  const [region, setRegion] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [pageLoading, setPageLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [refreshingPreview, setRefreshingPreview] = useState(false);
  const [localMessage, setLocalMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadBatches() {
      try {
        const result = await fetchImportBatches();
        if (!active) {
          return;
        }
        setBatches(result);
        if (result[0]) {
          setSelectedBatchId(result[0].id);
        }
      } finally {
        if (active) {
          setPageLoading(false);
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

    async function loadBatchState(batchId: string) {
      setRefreshingPreview(true);
      try {
        const [detailResult, previewResult] = await Promise.all([
          fetchImportBatch(batchId),
          fetchImportBatchPreview(batchId).catch(() => null),
        ]);
        if (!active) {
          return;
        }
        setSelectedBatch(detailResult);
        setPreview(previewResult);
      } finally {
        if (active) {
          setRefreshingPreview(false);
        }
      }
    }

    if (!selectedBatchId) {
      setSelectedBatch(null);
      setPreview(null);
      return;
    }

    void loadBatchState(selectedBatchId);
    return () => {
      active = false;
    };
  }, [selectedBatchId]);

  const selectedSourceFile = useMemo<SourceFilePreview | null>(() => preview?.source_files[0] ?? null, [preview]);
  const previewColumns = useMemo(() => {
    const firstRecord = selectedSourceFile?.preview_records[0];
    return firstRecord ? Object.keys(firstRecord.values) : [];
  }, [selectedSourceFile]);

  async function reloadBatches(selectBatchId?: string) {
    const result = await fetchImportBatches();
    setBatches(result);
    if (selectBatchId) {
      setSelectedBatchId(selectBatchId);
      return;
    }
    if (!selectedBatchId && result[0]) {
      setSelectedBatchId(result[0].id);
    }
  }

  async function handleCreateBatch() {
    if (files.length === 0) {
      setLocalMessage('请至少选择一个 Excel 文件。');
      return;
    }

    setSubmitting(true);
    setLocalMessage(null);
    try {
      const created = await createImportBatch({
        files,
        batchName,
        region,
        companyName,
      });
      const parsed = await parseImportBatch(created.id);
      setPreview(parsed);
      setSelectedBatchId(created.id);
      setSelectedBatch(created);
      await reloadBatches(created.id);
      setFiles([]);
      setBatchName('');
      setLocalMessage(`导入批次已创建：${created.batch_name}`);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleParseBatch(batchId: string) {
    setParsing(true);
    setLocalMessage(null);
    try {
      const parsed = await parseImportBatch(batchId);
      setPreview(parsed);
      setSelectedBatchId(batchId);
      setSelectedBatch(await fetchImportBatch(batchId));
      await reloadBatches(batchId);
      setLocalMessage('批次解析已刷新。');
    } finally {
      setParsing(false);
    }
  }

  return (
    <PageContainer
      eyebrow="Imports"
      title="导入批次"
      description="上传多个地区 Excel，创建导入批次，并快速查看首个文件的解析预览；更完整的文件级明细可进入批次详情页继续查看。"
      actions={
        <div className="button-row">
          <button type="button" className="button button--primary" onClick={() => void handleCreateBatch()} disabled={submitting}>
            {submitting ? '创建批次中...' : '创建导入批次'}
          </button>
          <button
            type="button"
            className="button button--ghost"
            onClick={() => (selectedBatchId ? void handleParseBatch(selectedBatchId) : undefined)}
            disabled={!selectedBatchId || parsing}
          >
            {parsing ? '刷新解析中...' : '刷新当前批次'}
          </button>
        </div>
      }
    >
      <div className="panel-grid panel-grid--two import-layout">
        <section className="panel-card import-uploader">
          <div>
            <span className="panel-label">上传入口</span>
            <strong>按批次接收 Excel 源文件</strong>
            <p>这里负责创建导入批次并触发首次解析，后续更完整的文件对比、映射检查和样本浏览都放到批次详情页里。</p>
          </div>
          <label className="form-field">
            <span>批次名称</span>
            <input value={batchName} onChange={(event) => setBatchName(event.target.value)} placeholder="例如 2026-02 社保导入" />
          </label>
          <div className="form-grid">
            <label className="form-field">
              <span>地区</span>
              <select value={region} onChange={(event) => setRegion(event.target.value)}>
                {PRESET_REGIONS.map((item) => (
                  <option key={item.value || 'auto'} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              <span>公司</span>
              <input value={companyName} onChange={(event) => setCompanyName(event.target.value)} placeholder="可选，便于回查" />
            </label>
          </div>
          <label className="upload-dropzone">
            <input
              type="file"
              accept=".xlsx,.xls"
              multiple
              onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
            />
            <strong>{files.length > 0 ? `已选择 ${files.length} 个文件` : '点击或拖拽上传 Excel 文件'}</strong>
            <span>支持 `.xlsx` / `.xls`，上传后会立即创建批次并进入解析预览。</span>
          </label>
          {files.length > 0 ? (
            <div className="file-chip-list">
              {files.map((file) => (
                <span key={`${file.name}-${file.size}`} className="file-chip">
                  {file.name}
                </span>
              ))}
            </div>
          ) : null}
          {localMessage ? <div className="inline-status inline-status--success">{localMessage}</div> : null}
        </section>

        <section className="panel-card import-batch-list">
          <div>
            <span className="panel-label">批次列表</span>
            <strong>{pageLoading ? '加载中...' : `${batches.length} 个批次`}</strong>
            <p>选择批次查看快速预览，或直接进入详情页查看每个文件的解析上下文。</p>
          </div>
          <div className="batch-list">
            {batches.length === 0 ? (
              <div className="status-item">当前还没有导入批次，请先上传文件。</div>
            ) : (
              batches.map((batch) => (
                <div key={batch.id} className={`batch-card batch-card--detail${selectedBatchId === batch.id ? ' is-active' : ''}`}>
                  <button type="button" className="batch-card__select" onClick={() => setSelectedBatchId(batch.id)}>
                    <strong>{batch.batch_name}</strong>
                    <span>{batch.status}</span>
                    <small>{batch.file_count} 个文件 · {formatDateTime(batch.updated_at)}</small>
                  </button>
                  <Link to={`/imports/${batch.id}`} className="batch-card__link">
                    查看详情
                  </Link>
                </div>
              ))
            )}
          </div>
        </section>
      </div>

      <div className="panel-grid panel-grid--two import-summary-grid">
        <article className="panel-card panel-card--soft">
          <span className="panel-label">当前批次</span>
          <strong>{selectedBatch?.batch_name ?? '尚未选择批次'}</strong>
          <p>
            {selectedBatch
              ? `${selectedBatch.file_count} 个文件，当前状态为 ${selectedBatch.status}。`
              : '从右侧批次列表中选择一个批次，即可在这里看到快速摘要。'}
          </p>
          {selectedBatch ? (
            <Link to={`/imports/${selectedBatch.id}`} className="inline-link">
              打开批次详情页
            </Link>
          ) : null}
        </article>
        <article className="panel-card panel-card--soft">
          <span className="panel-label">首个命中文件</span>
          <strong>{selectedSourceFile ? selectedSourceFile.raw_sheet_name : '尚未解析'}</strong>
          <p>
            {selectedSourceFile
              ? `${selectedSourceFile.normalized_record_count} 条标准化记录，过滤 ${selectedSourceFile.filtered_row_count} 条非明细行。`
              : '解析完成后，这里会显示首个文件的快速概览。'}
          </p>
        </article>
      </div>

      <div className="panel-card">
        <div className="section-heading">
          <div>
            <span className="panel-label">快速预览</span>
            <h2>当前批次首个文件</h2>
          </div>
          <div className="button-row">
            {refreshingPreview ? <span className="pill">预览刷新中</span> : null}
            {selectedBatch ? (
              <Link to={`/imports/${selectedBatch.id}`} className="button button--ghost">
                进入完整详情
              </Link>
            ) : null}
          </div>
        </div>
        {selectedSourceFile ? (
          <div className="source-file-grid">
            <div className="status-item">
              <strong>{selectedSourceFile.file_name}</strong>
              <div>sheet: {selectedSourceFile.raw_sheet_name}</div>
              <div>region: {selectedSourceFile.region ?? '未指定'}</div>
              <div>company: {selectedSourceFile.company_name ?? '未指定'}</div>
            </div>
            <div className="status-item">
              <strong>表头签名</strong>
              <div>{selectedSourceFile.raw_header_signature}</div>
            </div>
            <div className="status-item">
              <strong>未识别字段</strong>
              <div>{selectedSourceFile.unmapped_headers.length > 0 ? selectedSourceFile.unmapped_headers.join(' / ') : '无'}</div>
            </div>
          </div>
        ) : (
          <div className="status-item">当前批次还没有预览结果。你可以先刷新解析或进入详情页查看更完整状态。</div>
        )}
      </div>

      <div className="panel-grid panel-grid--two import-detail-grid">
        <section className="panel-card">
          <div className="section-heading">
            <div>
              <span className="panel-label">表头映射</span>
              <h2>快速查看规则命中</h2>
            </div>
          </div>
          {selectedSourceFile?.header_mappings.length ? (
            <div className="mapping-list">
              {selectedSourceFile.header_mappings.slice(0, 8).map((mapping) => (
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
            <div className="status-item">当前还没有映射结果。</div>
          )}
        </section>

        <section className="panel-card">
          <div className="section-heading">
            <div>
              <span className="panel-label">非明细行</span>
              <h2>快速过滤检查</h2>
            </div>
          </div>
          {selectedSourceFile?.filtered_rows.length ? (
            <div className="filtered-list">
              {selectedSourceFile.filtered_rows.slice(0, 8).map((row) => (
                <div key={`${row.row_number}-${row.reason}`} className="filtered-row-card">
                  <strong>第 {row.row_number} 行</strong>
                  <span>{row.reason}</span>
                  <small>{row.first_value}</small>
                </div>
              ))}
            </div>
          ) : (
            <div className="status-item">当前没有检测到被过滤的非明细行。</div>
          )}
        </section>
      </div>

      <div className="panel-card">
        <div className="section-heading">
          <div>
            <span className="panel-label">样本记录</span>
            <h2>前 20 行标准化预览</h2>
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
          <div className="status-item">当前没有可展示的标准化样本。</div>
        )}
      </div>
    </PageContainer>
  );
}
