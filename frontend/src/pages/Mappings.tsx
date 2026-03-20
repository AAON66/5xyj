import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import { PageContainer } from '../components';
import { fetchImportBatch, fetchImportBatches, type ImportBatchDetail, type ImportBatchSummary } from '../services/imports';
import { fetchHeaderMappings, updateHeaderMapping, type HeaderMappingItem } from '../services/mappings';

function mappingLabel(value: string): string {
  switch (value) {
    case 'rule':
      return '规则命中';
    case 'llm':
      return 'LLM 兜底';
    case 'manual':
      return '人工修正';
    case 'unmapped':
      return '未识别';
    default:
      return value;
  }
}

export function MappingsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [batches, setBatches] = useState<ImportBatchSummary[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(searchParams.get('batchId'));
  const [selectedSourceFileId, setSelectedSourceFileId] = useState<string | null>(searchParams.get('sourceFileId'));
  const [batchDetail, setBatchDetail] = useState<ImportBatchDetail | null>(null);
  const [mappings, setMappings] = useState<HeaderMappingItem[]>([]);
  const [availableFields, setAvailableFields] = useState<string[]>([]);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [panelMessage, setPanelMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadBatches() {
      try {
        const result = await fetchImportBatches();
        if (!active) {
          return;
        }
        setBatches(result);
        const initialBatchId = searchParams.get('batchId') ?? result[0]?.id ?? null;
        setSelectedBatchId((current) => current ?? initialBatchId);
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
  }, [searchParams]);

  useEffect(() => {
    let active = true;

    async function loadBatchContext(batchId: string) {
      const [detail, mappingPayload] = await Promise.all([
        fetchImportBatch(batchId),
        fetchHeaderMappings(batchId, selectedSourceFileId ?? undefined),
      ]);
      if (!active) {
        return;
      }

      setBatchDetail(detail);
      setMappings(mappingPayload.items);
      setAvailableFields(mappingPayload.available_canonical_fields);
      const nextSourceFileId = selectedSourceFileId ?? mappingPayload.items[0]?.source_file_id ?? detail.source_files[0]?.id ?? null;
      setSelectedSourceFileId(nextSourceFileId);
      setDrafts(
        Object.fromEntries(
          mappingPayload.items.map((item) => [item.id, item.canonical_field ?? ''])
        )
      );
    }

    if (!selectedBatchId) {
      setBatchDetail(null);
      setMappings([]);
      setAvailableFields([]);
      setDrafts({});
      return;
    }

    void loadBatchContext(selectedBatchId);
    return () => {
      active = false;
    };
  }, [selectedBatchId, selectedSourceFileId]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (selectedBatchId) {
      params.set('batchId', selectedBatchId);
    }
    if (selectedSourceFileId) {
      params.set('sourceFileId', selectedSourceFileId);
    }
    setSearchParams(params, { replace: true });
  }, [selectedBatchId, selectedSourceFileId, setSearchParams]);

  const sourceFiles = batchDetail?.source_files ?? [];
  const visibleMappings = useMemo(() => {
    if (!selectedSourceFileId) {
      return mappings;
    }
    return mappings.filter((item) => item.source_file_id === selectedSourceFileId);
  }, [mappings, selectedSourceFileId]);

  const summary = useMemo(() => {
    return {
      total: visibleMappings.length,
      manual: visibleMappings.filter((item) => item.mapping_source === 'manual' || item.manually_overridden).length,
      unmapped: visibleMappings.filter((item) => !item.canonical_field).length,
    };
  }, [visibleMappings]);

  async function handleSave(mapping: HeaderMappingItem) {
    const nextValue = drafts[mapping.id] || null;
    setSavingId(mapping.id);
    setPanelMessage(null);
    try {
      const updated = await updateHeaderMapping(mapping.id, nextValue);
      setMappings((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setDrafts((current) => ({ ...current, [mapping.id]: updated.canonical_field ?? '' }));
      setPanelMessage(`已更新字段映射：${mapping.raw_header}`);
    } finally {
      setSavingId(null);
    }
  }

  return (
    <PageContainer
      eyebrow="Mappings"
      title="字段映射配置与人工修正"
      description="查看每个批次的表头归一化结果，对低置信度或未识别字段进行人工覆盖，并把修正结果持久化到后端。"
      actions={
        <div className="button-row">
          {selectedBatchId ? (
            <Link to={`/imports/${selectedBatchId}`} className="button button--ghost">
              返回批次详情
            </Link>
          ) : null}
        </div>
      }
    >
      <div className="panel-grid panel-grid--two mapping-config-grid">
        <section className="panel-card">
          <div>
            <span className="panel-label">批次选择</span>
            <strong>{loading ? '加载中...' : `${batches.length} 个批次`}</strong>
            <p>先选择批次，再按文件切换需要修正的表头映射。</p>
          </div>
          <label className="form-field">
            <span>导入批次</span>
            <select value={selectedBatchId ?? ''} onChange={(event) => setSelectedBatchId(event.target.value || null)}>
              <option value="">请选择批次</option>
              {batches.map((batch) => (
                <option key={batch.id} value={batch.id}>
                  {batch.batch_name}
                </option>
              ))}
            </select>
          </label>
          <label className="form-field">
            <span>源文件</span>
            <select value={selectedSourceFileId ?? ''} onChange={(event) => setSelectedSourceFileId(event.target.value || null)} disabled={!sourceFiles.length}>
              <option value="">全部文件</option>
              {sourceFiles.map((file) => (
                <option key={file.id} value={file.id}>
                  {file.file_name}
                </option>
              ))}
            </select>
          </label>
          {panelMessage ? <div className="inline-status inline-status--success">{panelMessage}</div> : null}
        </section>

        <section className="panel-card mapping-summary-grid">
          <article className="status-item">
            <strong>{summary.total}</strong>
            <div>当前映射条目</div>
          </article>
          <article className="status-item">
            <strong>{summary.manual}</strong>
            <div>人工修正条目</div>
          </article>
          <article className="status-item">
            <strong>{summary.unmapped}</strong>
            <div>仍未识别条目</div>
          </article>
        </section>
      </div>

      <section className="panel-card">
        <div className="section-heading">
          <div>
            <span className="panel-label">映射清单</span>
            <h2>逐条检查并覆盖</h2>
          </div>
        </div>
        {visibleMappings.length ? (
          <div className="mapping-editor-list">
            {visibleMappings.map((mapping) => (
              <article key={mapping.id} className="mapping-editor-card">
                <div className="mapping-editor-card__head">
                  <div>
                    <strong>{mapping.raw_header}</strong>
                    <p>{mapping.raw_header_signature}</p>
                  </div>
                  <span className={`mapping-badge${mapping.canonical_field ? '' : ' mapping-badge--warn'}`}>
                    {mapping.canonical_field ?? '未识别'}
                  </span>
                </div>
                <div className="mapping-editor-meta">
                  <span>来源：{mappingLabel(mapping.mapping_source)}</span>
                  <span>文件：{mapping.source_file_name}</span>
                  <span>{mapping.confidence !== null ? `置信度 ${mapping.confidence.toFixed(2)}` : '无置信度'}</span>
                </div>
                <div className="candidate-chip-list">
                  {mapping.candidate_fields.length ? (
                    mapping.candidate_fields.map((field) => (
                      <span key={`${mapping.id}-${field}`} className="file-chip">
                        {field}
                      </span>
                    ))
                  ) : (
                    <span className="file-chip">暂无候选字段</span>
                  )}
                </div>
                <div className="mapping-editor-actions">
                  <label className="form-field">
                    <span>标准字段</span>
                    <select
                      value={drafts[mapping.id] ?? ''}
                      onChange={(event) => setDrafts((current) => ({ ...current, [mapping.id]: event.target.value }))}
                    >
                      <option value="">保持未识别</option>
                      {availableFields.map((field) => (
                        <option key={field} value={field}>
                          {field}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button
                    type="button"
                    className="button button--primary"
                    onClick={() => void handleSave(mapping)}
                    disabled={savingId === mapping.id}
                  >
                    {savingId === mapping.id ? '保存中...' : '保存修正'}
                  </button>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="status-item">当前批次还没有可修正的映射记录。请先完成解析，或切换到有预览结果的文件。</div>
        )}
      </section>
    </PageContainer>
  );
}
