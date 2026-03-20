import { useEffect, useMemo, useState } from 'react';

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
  { value: '', label: '???? / ????' },
  { value: 'guangzhou', label: '??' },
  { value: 'hangzhou', label: '??' },
  { value: 'xiamen', label: '??' },
  { value: 'shenzhen', label: '??' },
  { value: 'wuhan', label: '??' },
  { value: 'changsha', label: '??' },
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
    return '?';
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
    return `???: ${mapping.candidate_fields.join(', ')}`;
  }
  return '???';
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
      setLocalMessage('???????? Excel ???');
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
      setLocalMessage(`?????????${created.batch_name}`);
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
      setLocalMessage('??????????????');
    } finally {
      setParsing(false);
    }
  }

  return (
    <PageContainer
      eyebrow="Imports"
      title="???????"
      description="??????????????????????????????????????????"
      actions={
        <div className="button-row">
          <button type="button" className="button button--primary" onClick={() => void handleCreateBatch()} disabled={submitting}>
            {submitting ? '??????...' : '???????'}
          </button>
          <button
            type="button"
            className="button button--ghost"
            onClick={() => (selectedBatchId ? void handleParseBatch(selectedBatchId) : undefined)}
            disabled={!selectedBatchId || parsing}
          >
            {parsing ? '?????...' : '????????'}
          </button>
        </div>
      }
    >
      <div className="panel-grid panel-grid--two import-layout">
        <section className="panel-card import-uploader">
          <div>
            <span className="panel-label">????</span>
            <strong>?? Excel ???????</strong>
            <p>????????????????????????????????????????????</p>
          </div>
          <label className="form-field">
            <span>????</span>
            <input value={batchName} onChange={(event) => setBatchName(event.target.value)} placeholder="???2026-02 ????" />
          </label>
          <div className="form-grid">
            <label className="form-field">
              <span>??</span>
              <select value={region} onChange={(event) => setRegion(event.target.value)}>
                {PRESET_REGIONS.map((item) => (
                  <option key={item.value || 'auto'} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              <span>??</span>
              <input value={companyName} onChange={(event) => setCompanyName(event.target.value)} placeholder="???????" />
            </label>
          </div>
          <label className="upload-dropzone">
            <input
              type="file"
              accept=".xlsx,.xls"
              multiple
              onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
            />
            <strong>{files.length > 0 ? `??? ${files.length} ???` : '??????? Excel ??'}</strong>
            <span>?? `.xlsx` / `.xls`??????????????????????</span>
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
            <span className="panel-label">????</span>
            <strong>{pageLoading ? '???...' : `${batches.length} ???`}</strong>
            <p>??????????????????????????????????</p>
          </div>
          <div className="batch-list">
            {batches.length === 0 ? (
              <div className="status-item">??????????????????</div>
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
                  <small>{batch.file_count} ??? ? {formatDateTime(batch.updated_at)}</small>
                </button>
              ))
            )}
          </div>
        </section>
      </div>

      <div className="panel-grid panel-grid--two import-summary-grid">
        <article className="panel-card panel-card--soft">
          <span className="panel-label">????</span>
          <strong>{selectedBatch?.batch_name ?? '?????'}</strong>
          <p>
            {selectedBatch
              ? `${selectedBatch.file_count} ?????? ${selectedBatch.status}?`
              : '???????????????????????'}
          </p>
        </article>
        <article className="panel-card panel-card--soft">
          <span className="panel-label">????</span>
          <strong>{selectedSourceFile ? selectedSourceFile.raw_sheet_name : '????'}</strong>
          <p>
            {selectedSourceFile
              ? `${selectedSourceFile.normalized_record_count} ????????? ${selectedSourceFile.filtered_row_count} ??????`
              : '?????????????????????????'}
          </p>
        </article>
      </div>

      <div className="panel-card">
        <div className="section-heading">
          <div>
            <span className="panel-label">???</span>
            <h2>????????</h2>
          </div>
          {refreshingPreview ? <span className="pill">???</span> : null}
        </div>
        {selectedSourceFile ? (
          <div className="source-file-grid">
            <div className="status-item">
              <strong>{selectedSourceFile.file_name}</strong>
              <div>sheet: {selectedSourceFile.raw_sheet_name}</div>
              <div>region: {selectedSourceFile.region ?? '???'}</div>
              <div>company: {selectedSourceFile.company_name ?? '???'}</div>
            </div>
            <div className="status-item">
              <strong>????</strong>
              <div>{selectedSourceFile.raw_header_signature}</div>
            </div>
            <div className="status-item">
              <strong>????</strong>
              <div>{selectedSourceFile.unmapped_headers.length > 0 ? selectedSourceFile.unmapped_headers.join(' / ') : '?'}</div>
            </div>
          </div>
        ) : (
          <div className="status-item">????????????????????????????????</div>
        )}
      </div>

      <div className="panel-grid panel-grid--two import-detail-grid">
        <section className="panel-card">
          <div className="section-heading">
            <div>
              <span className="panel-label">????</span>
              <h2>???????</h2>
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
                    ?? {mapping.mapping_source}
                    {mapping.confidence !== null ? ` ? ??? ${mapping.confidence.toFixed(2)}` : ''}
                    {mapping.llm_attempted ? ` ? LLM ${mapping.llm_status}` : ''}
                  </small>
                </article>
              ))}
            </div>
          ) : (
            <div className="status-item">?????????????????????</div>
          )}
        </section>

        <section className="panel-card">
          <div className="section-heading">
            <div>
              <span className="panel-label">????</span>
              <h2>????</h2>
            </div>
          </div>
          {selectedSourceFile?.filtered_rows.length ? (
            <div className="filtered-list">
              {selectedSourceFile.filtered_rows.map((row) => (
                <div key={`${row.row_number}-${row.reason}`} className="filtered-row-card">
                  <strong>? {row.row_number} ?</strong>
                  <span>{row.reason}</span>
                  <small>{row.first_value}</small>
                </div>
              ))}
            </div>
          ) : (
            <div className="status-item">?????????????????????</div>
          )}
        </section>
      </div>

      <div className="panel-card">
        <div className="section-heading">
          <div>
            <span className="panel-label">?????</span>
            <h2>? 20 ???</h2>
          </div>
        </div>
        {selectedSourceFile?.preview_records.length ? (
          <div className="preview-table-wrap">
            <table className="preview-table">
              <thead>
                <tr>
                  <th>???</th>
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
          <div className="status-item">?????????????????? 20 ??</div>
        )}
      </div>

      <div className="panel-card">
        <div className="section-heading">
          <div>
            <span className="panel-label">?????</span>
            <h2>??????????</h2>
          </div>
        </div>
        {selectedSourceFile?.preview_records.some((record) => Object.keys(record.unmapped_values).length > 0) ? (
          <div className="unmapped-grid">
            {selectedSourceFile.preview_records
              .filter((record) => Object.keys(record.unmapped_values).length > 0)
              .slice(0, 6)
              .map((record) => (
                <article key={`unmapped-${record.source_row_number}`} className="status-item">
                  <strong>? {record.source_row_number} ?</strong>
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
          <div className="status-item">?????????????????????</div>
        )}
      </div>
    </PageContainer>
  );
}
