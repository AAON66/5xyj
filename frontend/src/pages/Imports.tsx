import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { PageContainer, SectionState, SurfaceNotice } from '../components';
import { normalizeApiError } from '../services/api';
import {
  bulkDeleteImportBatches,
  createImportBatch,
  deleteImportBatch,
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
  const [deletingBatchId, setDeletingBatchId] = useState<string | null>(null);
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const [selectedBatchIds, setSelectedBatchIds] = useState<string[]>([]);
  const [refreshingPreview, setRefreshingPreview] = useState(false);
  const [localNotice, setLocalNotice] = useState<{ tone: 'success' | 'warning'; message: string } | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadBatches() {
      try {
        const result = await fetchImportBatches();
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
          setPageError('导入批次列表暂时加载失败，请稍后重试。');
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
        const detailResult = await fetchImportBatch(batchId);
        if (!active) {
          return;
        }
        const firstSourceFileId = detailResult.source_files[0]?.id;
        setSelectedBatch(detailResult);
        setPreview(null);
        setPageError(null);

        if (!firstSourceFileId || detailResult.status === 'uploaded') {
          return;
        }

        const previewResult = await fetchImportBatchPreview(batchId, { sourceFileId: firstSourceFileId }).catch(() => null);
        if (!active) {
          return;
        }
        setPreview(previewResult);
      } catch {
        if (active) {
          setPageError('当前批次详情加载失败，请重新选择批次或稍后重试。');
        }
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

  async function reloadBatches(selectBatchId?: string | null) {
    const result = await fetchImportBatches();
    setBatches(result);
    const availableIds = new Set(result.map((batch) => batch.id));
    setSelectedBatchIds((current) => current.filter((batchId) => availableIds.has(batchId)));
    if (selectBatchId !== undefined) {
      setSelectedBatchId(selectBatchId && availableIds.has(selectBatchId) ? selectBatchId : (result[0]?.id ?? null));
      return;
    }
    setSelectedBatchId((current) => {
      if (current && availableIds.has(current)) {
        return current;
      }
      return result[0]?.id ?? null;
    });
  }

  async function handleCreateBatch() {
    if (files.length === 0) {
      setLocalNotice({ tone: 'warning', message: '请至少选择一个 Excel 文件。' });
      return;
    }

    setSubmitting(true);
    setLocalNotice(null);
    try {
      const created = await createImportBatch({
        files,
        batchName,
        region,
        companyName,
      });
      const parsed = await parseImportBatch(created.id);
      setPreview({
        ...parsed,
        source_files: parsed.source_files.slice(0, 1),
      });
      setSelectedBatchId(created.id);
      setSelectedBatch(created);
      await reloadBatches(created.id);
      setFiles([]);
      setBatchName('');
      setLocalNotice({ tone: 'success', message: `导入批次已创建：${created.batch_name}` });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleParseBatch(batchId: string) {
    setParsing(true);
    setLocalNotice(null);
    try {
      const parsed = await parseImportBatch(batchId);
      setPreview({
        ...parsed,
        source_files: parsed.source_files.slice(0, 1),
      });
      setSelectedBatchId(batchId);
      setSelectedBatch(await fetchImportBatch(batchId));
      await reloadBatches(batchId);
      setLocalNotice({ tone: 'success', message: '批次解析已刷新。' });
    } finally {
      setParsing(false);
    }
  }

  async function handleDeleteBatch(batchId: string, batchName: string) {
    const confirmed = window.confirm(`确认删除批次“${batchName}”吗？这会同时删除已上传文件和相关导出结果，且无法撤销。`);
    if (!confirmed) {
      return;
    }

    setDeletingBatchId(batchId);
    setLocalNotice(null);
    try {
      await deleteImportBatch(batchId);
      await reloadBatches(selectedBatchId === batchId ? null : undefined);
      setSelectedBatchIds((current) => current.filter((currentId) => currentId !== batchId));
      setLocalNotice({ tone: 'success', message: `批次已删除：${batchName}` });
    } catch (error) {
      setLocalNotice({ tone: 'warning', message: normalizeApiError(error).message || '批次删除失败，请稍后重试。' });
    } finally {
      setDeletingBatchId(null);
    }
  }

  async function handleBulkDelete() {
    if (selectedBatchIds.length === 0) {
      setLocalNotice({ tone: 'warning', message: '请先勾选至少一个批次。' });
      return;
    }

    const confirmed = window.confirm(`确认批量删除 ${selectedBatchIds.length} 个批次吗？这会同时删除已上传文件和相关导出结果，且无法撤销。`);
    if (!confirmed) {
      return;
    }

    setBulkDeleting(true);
    setLocalNotice(null);
    try {
      const result = await bulkDeleteImportBatches(selectedBatchIds);
      const removedSelectedBatch = selectedBatchId ? selectedBatchIds.includes(selectedBatchId) : false;
      await reloadBatches(removedSelectedBatch ? null : undefined);
      setSelectedBatchIds([]);

      const missingMessage =
        result.missing_ids.length > 0 ? ` 未找到 ${result.missing_ids.length} 个批次：${result.missing_ids.join('、')}。` : '';
      setLocalNotice({
        tone: 'success',
        message: `已删除 ${result.deleted_count} 个批次。${missingMessage}`.trim(),
      });
    } catch (error) {
      setLocalNotice({ tone: 'warning', message: normalizeApiError(error).message || '批量删除失败，请稍后重试。' });
    } finally {
      setBulkDeleting(false);
    }
  }

  return (
    <PageContainer
      eyebrow="Imports"
      title="导入批次"
      description="上传多个地区 Excel，创建导入批次，并快速查看首个文件的解析预览；更完整的文件级明细可进入批次详情页继续查看。"
      actions={
        <div className="button-row">
          <button type="button" className="button button--primary" onClick={() => void handleCreateBatch()} disabled={submitting || bulkDeleting}>
            {submitting ? '创建批次中...' : '创建导入批次'}
          </button>
          <button
            type="button"
            className="button button--ghost"
            onClick={() => (selectedBatchId ? void handleParseBatch(selectedBatchId) : undefined)}
            disabled={!selectedBatchId || parsing || bulkDeleting || deletingBatchId !== null}
          >
            {parsing ? '刷新解析中...' : '刷新当前批次'}
          </button>
          <button
            type="button"
            className="button button--ghost"
            onClick={() => void handleBulkDelete()}
            disabled={selectedBatchIds.length === 0 || bulkDeleting || deletingBatchId !== null}
          >
            {bulkDeleting ? '批量删除中...' : `批量删除所选 (${selectedBatchIds.length})`}
          </button>
        </div>
      }
    >
      {localNotice ? <SurfaceNotice tone={localNotice.tone} message={localNotice.message} /> : null}
      {pageError ? <SurfaceNotice tone="error" title="页面状态异常" message={pageError} /> : null}

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
            <input type="file" accept=".xlsx,.xls" multiple onChange={(event) => setFiles(Array.from(event.target.files ?? []))} />
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
        </section>

        <section className="panel-card import-batch-list">
          <div>
            <span className="panel-label">批次列表</span>
            <strong>{pageLoading ? '加载中...' : `${batches.length} 个批次`}</strong>
            <p>选择批次查看快速预览，或直接进入详情页查看每个文件的解析上下文。</p>
          </div>
          {pageLoading ? (
            <SectionState title="正在加载批次" message="系统正在读取已有导入批次，请稍候。" />
          ) : batches.length === 0 ? (
            <SectionState title="还没有导入批次" message="上传第一批 Excel 后，这里会显示历史批次。" />
          ) : (
            <div className="batch-list">
              {batches.map((batch) => (
                <div key={batch.id} className={`batch-card batch-card--detail${selectedBatchId === batch.id ? ' is-active' : ''}`}>
                  <button type="button" className="batch-card__select" onClick={() => setSelectedBatchId(batch.id)}>
                    <strong>{batch.batch_name}</strong>
                    <span>{batch.status}</span>
                    <small>{batch.file_count} 个文件 · {formatDateTime(batch.updated_at)}</small>
                    <small>
                      <span className="batch-meta-label">操作人</span>
                      <span>{batch.created_by_name || '\u2014'}</span>
                      {' · '}
                      <span className="batch-meta-label">记录数</span>
                      <span>{batch.normalized_record_count ?? '-'}</span>
                    </small>
                  </button>
                  <div className="batch-card__footer">
                    <label className="batch-card__check">
                      <input
                        type="checkbox"
                        checked={selectedBatchIds.includes(batch.id)}
                        onChange={(event) =>
                          setSelectedBatchIds((current) =>
                            event.target.checked ? Array.from(new Set([...current, batch.id])) : current.filter((item) => item !== batch.id),
                          )
                        }
                        disabled={bulkDeleting}
                      />
                      <span>加入批量删除</span>
                    </label>
                    <div className="batch-card__actions">
                      <Link to={`/imports/${batch.id}`} className="batch-card__link">
                        查看详情
                      </Link>
                      <button
                        type="button"
                        className="batch-card__delete"
                        onClick={() => void handleDeleteBatch(batch.id, batch.batch_name)}
                        disabled={bulkDeleting || deletingBatchId !== null}
                      >
                        {deletingBatchId === batch.id ? '删除中...' : '删除批次'}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
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
        {!selectedSourceFile ? (
          <SectionState title="暂无解析预览" message="当前批次还没有预览结果，你可以先刷新解析或进入详情页查看更完整状态。" />
        ) : (
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
            <SectionState title="暂无映射结果" message="当前还没有表头映射结果。完成解析后，这里会展示规则或 LLM 的归一化命中。" />
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
            <SectionState title="没有过滤项" message="当前没有检测到需要剔除的合计、小计或分组标题行。" />
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
          <SectionState title="暂无标准化样本" message="当前没有可展示的标准化样本，先刷新解析结果后再查看。" />
        )}
      </div>
    </PageContainer>
  );
}
