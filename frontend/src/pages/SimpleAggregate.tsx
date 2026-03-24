import { useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react';
import { Link } from 'react-router-dom';

import { PageContainer, SectionState, SurfaceNotice } from '../components';
import { useAggregateSession } from '../hooks';
import { downloadAggregateArtifact, type AggregateArtifact, type AggregateProgressEvent } from '../services/aggregate';
import { cancelAggregateSession, clearAggregateSession, startAggregateSession } from '../services/aggregateSessionStore';
import { fetchEmployeeMasters } from '../services/employees';
import { fetchSystemHealth, type SystemHealth } from '../services/system';

const TEXT = {
  eyebrow: 'Quick Aggregate',
  title: '上传后直接导出两份结果',
  description:
    '默认走完整主链路：自动识别社保与公积金表头、过滤非明细行、执行校验和工号匹配，最后同时输出薪酬模板和工具表最终版。',
  start: '开始聚合并导出',
  running: '正在聚合...',
  cancel: '取消当前聚合',
  clear: '清除当前记录',
  advanced: '进入高级页面',
  backendReady: '后端已就绪',
  failedTitle: '本次聚合失败',
  successTitle: '两份文件已生成',
  masterTitle: '已同步导入员工主档',
  blockedTitle: '链路已继续但需要关注',
  stepOne: '步骤 1',
  stepTwo: '步骤 2',
  chooseFiles: '选择文件',
  results: '直接查看结果',
  socialEyebrow: '社保明细',
  socialTitle: '社保文件',
  housingEyebrow: '公积金明细',
  housingTitle: '公积金文件',
  employeeEyebrow: '员工主档',
  employeeTitle: '可选主数据',
  employeeHint: '可以与本次聚合一起上传，用于工号匹配。',
  employeeMode: '\u4e3b\u6863\u6765\u6e90',
  employeeModeNone: '\u672c\u6b21\u4e0d\u4f7f\u7528',
  employeeModeExisting: '\u4f7f\u7528\u670d\u52a1\u5668\u5df2\u6709\u4e3b\u6863',
  employeeModeUpload: '\u4e0a\u4f20\u65b0\u4e3b\u6863',
  employeeExistingLoading: '\u6b63\u5728\u8bfb\u53d6\u670d\u52a1\u5668\u5df2\u6709\u4e3b\u6863...',
  employeeExistingEmpty: '\u5f53\u524d\u670d\u52a1\u5668\u8fd8\u6ca1\u6709\u53ef\u7528\u7684\u5458\u5de5\u4e3b\u6863\u3002',
  employeeExistingReady: '\u672c\u6b21\u5c06\u76f4\u63a5\u4f7f\u7528\u670d\u52a1\u5668\u73b0\u6709\u7684\u5728\u804c\u5458\u5de5\u4e3b\u6863\u8fdb\u884c\u5de5\u53f7\u5339\u914d\u3002',
  employeeNoneMessage: '\u672c\u6b21\u5c06\u4e0d\u4f7f\u7528\u5458\u5de5\u4e3b\u6863\uff0c\u4ecd\u53ef\u4ee5\u7ee7\u7eed\u805a\u5408\u5e76\u5bfc\u51fa\u7ed3\u679c\u3002',
  metaTitle: '批次设置',
  addFiles: '添加文件',
  clearFiles: '清空列表',
  delete: '删除',
  selectedFiles: '已选文件',
  noSocial: '还没有选择社保文件。',
  noHousing: '还没有选择公积金文件。',
  noEmployee: '未附带员工主档，也可以先直接导出结果。',
  addMaster: '添加主档',
  replaceMaster: '重新选择',
  removeMaster: '删除文件',
  batchName: '批次名称（可选）',
  batchPlaceholder: '例如：2026-02 社保公积金聚合',
  batchTip: '聚合开始后可以切换到其他页面，这里会保留本次记录，直到你主动取消或清除。',
  selectionRequired: '请至少选择一个社保或公积金 Excel 文件。',
  employeeExistingRequired: '\u5f53\u524d\u8fd8\u6ca1\u6709\u53ef\u7528\u7684\u670d\u52a1\u5668\u5458\u5de5\u4e3b\u6863\uff0c\u8bf7\u5148\u4e0a\u4f20\u65b0\u4e3b\u6863\u6216\u5207\u6362\u4e3a\u4e0d\u4f7f\u7528\u3002',
  employeeUploadRequired: '\u4f60\u5df2\u9009\u62e9\u201c\u4e0a\u4f20\u65b0\u4e3b\u6863\u201d\uff0c\u8bf7\u5148\u9009\u62e9\u4e00\u4e2a\u5458\u5de5\u4e3b\u6863\u6587\u4ef6\u3002',
  waitingTitle: '等你开始聚合',
  waitingMessage: '上传社保、公积金文件后，这里会直接显示进度、双模板结果和下载入口。',
  exportStatus: '导出状态',
  normalizedCount: '聚合后记录数',
  filteredCount: '已过滤非明细行',
  matchedCount: '匹配成功记录',
  download: '下载文件',
  persistedRecord: '记录已保留',
  batchIdPending: '批次编号生成中',
  done: '已完成',
  active: '进行中',
  pending: '等待中',
  unknownRegion: '未识别地区',
  unknownCompany: '未识别公司',
  socialKind: '社保',
  housingKind: '公积金',
  parseOverview: '解析总览',
  parseTotalFiles: '总文件数',
  parseWorkers: '并行路数',
  parseQueued: '排队中',
  parseRunning: '解析中',
  parseAnalyzed: '待保存',
  parseSaved: '已保存',
  parseSheet: '工作表',
  parseRecords: '明细',
  parseFiltered: '过滤',
  parseUnmapped: '未识别表头',
  phaseQueued: '排队中',
  phaseStarted: '解析中',
  phaseAnalyzed: '待保存',
  phaseSaved: '已保存',
  activeParallel: '当前并行解析',
  activeIdle: '当前没有文件处于解析中，系统会自动补上下一个排队文件。',
};

const PROGRESS_STEPS = [
  { key: 'employee_import', label: '员工主档' },
  { key: 'batch_upload', label: '上传批次' },
  { key: 'parse', label: '解析识别' },
  { key: 'validate', label: '数据校验' },
  { key: 'match', label: '工号匹配' },
  { key: 'export', label: '双模板导出' },
] as const;

interface UploadEntry {
  id: string;
  name: string;
  meta: string;
}

interface UploadPanelProps {
  eyebrow: string;
  title: string;
  entries: UploadEntry[];
  onAdd: () => void;
  onClear: () => void;
  onRemove: (entryId: string) => void;
  emptyMessage: string;
  tone: 'social' | 'housing';
  disabled: boolean;
}

function artifactLabel(value: string): string {
  return value === 'salary' ? '薪酬模板' : '工具表最终版';
}

function artifactTone(artifact: AggregateArtifact): 'success' | 'warning' | 'error' {
  if (artifact.status === 'completed') {
    return 'success';
  }
  if (artifact.status === 'failed') {
    return 'error';
  }
  return 'warning';
}

function statusLabel(value: string | null): string {
  switch (value) {
    case 'completed':
    case 'exported':
      return '已完成';
    case 'failed':
      return '已失败';
    case 'matched':
      return '已匹配';
    case 'validated':
      return '已校验';
    case 'normalized':
      return '已标准化';
    default:
      return value ?? '-';
  }
}

function formatArtifactMessage(artifact: AggregateArtifact): string {
  const path = artifact.file_path ?? artifact.error_message ?? '暂无输出路径';
  if (artifact.row_count > 0 && artifact.file_path) {
    return `${path} | ${artifact.row_count} 行`;
  }
  return path;
}

function getStepState(stepKey: string, progress: AggregateProgressEvent | null): 'done' | 'active' | 'pending' {
  if (!progress) {
    return 'pending';
  }

  const currentIndex = PROGRESS_STEPS.findIndex((item) => item.key === progress.stage);
  const targetIndex = PROGRESS_STEPS.findIndex((item) => item.key === stepKey);
  if (currentIndex === -1 || targetIndex === -1) {
    return 'pending';
  }
  if (targetIndex < currentIndex || (targetIndex === currentIndex && progress.percent >= 100)) {
    return 'done';
  }
  if (targetIndex == currentIndex) {
    return 'active';
  }
  return 'pending';
}

function sourceKindLabel(value: string): string {
  return value === 'housing_fund' ? TEXT.housingKind : TEXT.socialKind;
}

function parsePhaseLabel(value: string): string {
  switch (value) {
    case 'parse_queued':
      return TEXT.phaseQueued;
    case 'parse_started':
      return TEXT.phaseStarted;
    case 'parse_analyzed':
      return TEXT.phaseAnalyzed;
    case 'parse_saved':
      return TEXT.phaseSaved;
    default:
      return TEXT.active;
  }
}

function parsePhaseTone(value: string): 'queued' | 'running' | 'analyzed' | 'saved' {
  switch (value) {
    case 'parse_saved':
      return 'saved';
    case 'parse_analyzed':
      return 'analyzed';
    case 'parse_started':
      return 'running';
    default:
      return 'queued';
  }
}

function formatParseFileMeta(progress: NonNullable<AggregateProgressEvent['parse_files']>[number]): string {
  const parts = [
    sourceKindLabel(progress.source_kind ?? 'social_security'),
    progress.region ?? TEXT.unknownRegion,
    progress.company_name ?? TEXT.unknownCompany,
  ];
  if (typeof progress.normalized_record_count === 'number') {
    parts.push(`${TEXT.parseRecords} ${progress.normalized_record_count}`);
  }
  if (typeof progress.filtered_row_count === 'number') {
    parts.push(`${TEXT.parseFiltered} ${progress.filtered_row_count}`);
  }
  if (typeof progress.unmapped_header_count === 'number') {
    parts.push(`${TEXT.parseUnmapped} ${progress.unmapped_header_count}`);
  }
  return parts.join(' / ');
}

function fileKey(file: File): string {
  return `${file.name}_${file.size}_${file.lastModified}`;
}

function mergeFiles(existing: File[], incoming: File[]): File[] {
  if (!incoming.length) {
    return existing;
  }

  const merged = [...existing];
  const known = new Set(existing.map((file) => fileKey(file)));
  incoming.forEach((file) => {
    const key = fileKey(file);
    if (!known.has(key)) {
      known.add(key);
      merged.push(file);
    }
  });
  return merged;
}

function formatFileSize(size: number): string {
  if (size >= 1024 * 1024) {
    return `${(size / (1024 * 1024)).toFixed(2)} MB`;
  }
  if (size >= 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${size} B`;
}

function mapFilesToEntries(files: File[]): UploadEntry[] {
  return files.map((file) => ({ id: fileKey(file), name: file.name, meta: formatFileSize(file.size) }));
}

function mapNamesToEntries(names: string[]): UploadEntry[] {
  return names.map((name, index) => ({ id: `${name}_${index}`, name, meta: TEXT.persistedRecord }));
}

function triggerBlobDownload(blob: Blob, fileName: string): void {
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.URL.revokeObjectURL(url);
}

function UploadPanel({ eyebrow, title, entries, onAdd, onClear, onRemove, emptyMessage, tone, disabled }: UploadPanelProps) {
  return (
    <article className={`upload-panel upload-panel--${tone}`}>
      <div className="upload-panel__header upload-panel__header--aligned">
        <div>
          <span className="panel-label">{eyebrow}</span>
          <h3>{title}</h3>
        </div>
        <div className="upload-panel__summary">
          <strong>{entries.length}</strong>
          <span>{TEXT.selectedFiles}</span>
        </div>
      </div>
      <div className="upload-panel__actions button-row">
        <button type="button" className="button button--primary" onClick={onAdd} disabled={disabled}>
          {TEXT.addFiles}
        </button>
        <button type="button" className="button button--ghost" onClick={onClear} disabled={disabled || !entries.length}>
          {TEXT.clearFiles}
        </button>
      </div>
      {entries.length ? (
        <div className="upload-file-list">
          {entries.map((entry) => (
            <div key={entry.id} className="upload-file-chip">
              <div className="upload-file-chip__meta">
                <strong>{entry.name}</strong>
                <span>{entry.meta}</span>
              </div>
              <button type="button" className="button button--ghost upload-file-chip__remove" onClick={() => onRemove(entry.id)} disabled={disabled}>
                {TEXT.delete}
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="upload-panel__empty">{emptyMessage}</div>
      )}
    </article>
  );
}

export function SimpleAggregatePage() {
  const aggregateSession = useAggregateSession();
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [existingEmployeeMasterCount, setExistingEmployeeMasterCount] = useState(0);
  const [loadingEmployeeMasters, setLoadingEmployeeMasters] = useState(true);
  const [socialFiles, setSocialFiles] = useState<File[]>([]);
  const [housingFundFiles, setHousingFundFiles] = useState<File[]>([]);
  const [employeeMasterFile, setEmployeeMasterFile] = useState<File | null>(null);
  const [employeeMasterMode, setEmployeeMasterMode] = useState<'none' | 'upload' | 'existing'>('none');
  const [batchName, setBatchName] = useState('');
  const [selectionError, setSelectionError] = useState<string | null>(null);
  const [downloadingTemplate, setDownloadingTemplate] = useState<string | null>(null);

  const socialInputRef = useRef<HTMLInputElement | null>(null);
  const housingInputRef = useRef<HTMLInputElement | null>(null);
  const employeeInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    let active = true;
    fetchSystemHealth()
      .then((payload) => {
        if (active) {
          setHealth(payload);
        }
      })
      .catch(() => {
        if (active) {
          setHealth(null);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    setLoadingEmployeeMasters(true);
    fetchEmployeeMasters({ activeOnly: true })
      .then((payload) => {
        if (active) {
          setExistingEmployeeMasterCount(payload.total);
        }
      })
      .catch(() => {
        if (active) {
          setExistingEmployeeMasterCount(0);
        }
      })
      .finally(() => {
        if (active) {
          setLoadingEmployeeMasters(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const running = aggregateSession.status === 'running';
  const hasSessionRecord = aggregateSession.status !== 'idle';
  const progress = aggregateSession.progress;
  const result = aggregateSession.result;
  const pageError = selectionError ?? aggregateSession.error;
  const lockSelection = hasSessionRecord;
  const effectiveEmployeeMasterMode = hasSessionRecord ? aggregateSession.selection.employeeMasterMode : employeeMasterMode;

  const outputArtifacts = useMemo(() => result?.artifacts ?? [], [result]);
  const normalizedCount = useMemo(() => result?.source_files.reduce((sum, item) => sum + item.normalized_record_count, 0) ?? 0, [result]);
  const filteredCount = useMemo(() => result?.source_files.reduce((sum, item) => sum + item.filtered_row_count, 0) ?? 0, [result]);
  const parseSummary = progress?.parse_summary;
  const parseFiles = progress?.parse_files ?? [];
  const activeParseFiles = useMemo(
    () => parseFiles.filter((item) => item.phase === 'parse_started').slice(0, parseSummary?.worker_count ?? 5),
    [parseFiles, parseSummary?.worker_count],
  );

  const socialEntries = useMemo(() => {
    if (hasSessionRecord && !socialFiles.length) {
      return mapNamesToEntries(aggregateSession.selection.socialFiles);
    }
    return mapFilesToEntries(socialFiles);
  }, [aggregateSession.selection.socialFiles, hasSessionRecord, socialFiles]);

  const housingEntries = useMemo(() => {
    if (hasSessionRecord && !housingFundFiles.length) {
      return mapNamesToEntries(aggregateSession.selection.housingFundFiles);
    }
    return mapFilesToEntries(housingFundFiles);
  }, [aggregateSession.selection.housingFundFiles, hasSessionRecord, housingFundFiles]);

  function handleSocialFilesSelected(event: ChangeEvent<HTMLInputElement>) {
    const selectedFiles = Array.from(event.target.files ?? []);
    event.target.value = '';
    setSelectionError(null);
    setSocialFiles((current) => mergeFiles(current, selectedFiles));
  }

  function handleHousingFilesSelected(event: ChangeEvent<HTMLInputElement>) {
    const selectedFiles = Array.from(event.target.files ?? []);
    event.target.value = '';
    setSelectionError(null);
    setHousingFundFiles((current) => mergeFiles(current, selectedFiles));
  }

  function handleEmployeeMasterSelected(event: ChangeEvent<HTMLInputElement>) {
    const selectedFile = event.target.files?.[0] ?? null;
    event.target.value = '';
    setSelectionError(null);
    setEmployeeMasterFile(selectedFile);
    if (selectedFile) {
      setEmployeeMasterMode('upload');
    }
  }

  function removeSocialFile(targetId: string) {
    setSocialFiles((current) => current.filter((file) => fileKey(file) !== targetId));
  }

  function removeHousingFile(targetId: string) {
    setHousingFundFiles((current) => current.filter((file) => fileKey(file) !== targetId));
  }

  async function handleRun() {
    if (!socialFiles.length && !housingFundFiles.length) {
      setSelectionError(TEXT.selectionRequired);
      return;
    }
    if (employeeMasterMode === 'existing' && existingEmployeeMasterCount <= 0) {
      setSelectionError(TEXT.employeeExistingRequired);
      return;
    }
    if (employeeMasterMode === 'upload' && !employeeMasterFile) {
      setSelectionError(TEXT.employeeUploadRequired);
      return;
    }

    setSelectionError(null);
    try {
      await startAggregateSession({
        files: socialFiles,
        housingFundFiles,
        employeeMasterFile: employeeMasterMode === 'upload' ? employeeMasterFile : null,
        employeeMasterMode,
        batchName,
      });
    } catch {
      return;
    }
  }

  function handleClearRecord() {
    clearAggregateSession();
    setSelectionError(null);
  }

  async function handleDownloadArtifact(templateType: string) {
    if (!result?.batch_id) {
      return;
    }

    setDownloadingTemplate(templateType);
    setSelectionError(null);
    try {
      const { blob, fileName } = await downloadAggregateArtifact(result.batch_id, templateType);
      triggerBlobDownload(blob, fileName);
    } catch (error) {
      setSelectionError(error instanceof Error ? error.message : '下载失败，请稍后重试。');
    } finally {
      setDownloadingTemplate(null);
    }
  }

  const canStart = !running && !hasSessionRecord && (socialFiles.length > 0 || housingFundFiles.length > 0);
  const employeeDisplayName =
    effectiveEmployeeMasterMode === 'upload' ? (employeeMasterFile?.name ?? aggregateSession.selection.employeeMasterFile) : null;

  return (
    <PageContainer
      eyebrow={TEXT.eyebrow}
      title={TEXT.title}
      description={TEXT.description}
      actions={
        <div className="button-row">
          <button type="button" className="button button--primary" disabled={!canStart} onClick={() => void handleRun()}>
            {running ? (
              <span className="loading-inline">
                <span className="loading-inline__spinner" aria-hidden="true" />
                {TEXT.running}
              </span>
            ) : (
              TEXT.start
            )}
          </button>
          {running ? (
            <button type="button" className="button button--ghost" onClick={cancelAggregateSession}>
              {TEXT.cancel}
            </button>
          ) : null}
          {!running && hasSessionRecord ? (
            <button type="button" className="button button--ghost" onClick={handleClearRecord}>
              {TEXT.clear}
            </button>
          ) : null}
          <Link to="/imports" className="button button--ghost">
            {TEXT.advanced}
          </Link>
        </div>
      }
    >
      {health ? (
        <SurfaceNotice tone="success" title={'后端已就绪'} message={`社保表格聚合工具 ${health.version} | /api/v1/system/health 响应正常`} />
      ) : null}
      {pageError ? <SurfaceNotice tone="error" title={TEXT.failedTitle} message={pageError} /> : null}
      {result && result.export_status === 'completed' ? (
        <SurfaceNotice tone="success" title={TEXT.successTitle} message={`批次 ${result.batch_name} 已完成双模板导出。`} />
      ) : null}
      {result && result.employee_master ? (
        <SurfaceNotice tone="info" title={TEXT.masterTitle} message={`${result.employee_master.file_name} | 新增 ${result.employee_master.created_count} | 更新 ${result.employee_master.updated_count}`} />
      ) : null}
      {result && result.blocked_reason ? <SurfaceNotice tone="warning" title={TEXT.blockedTitle} message={result.blocked_reason} /> : null}

      <div className="panel-grid panel-grid--two simple-aggregate-grid">
        <section className="panel-card simple-aggregate-card">
          <div className="section-heading">
            <div>
              <span className="panel-label">{TEXT.stepOne}</span>
              <h2>{TEXT.chooseFiles}</h2>
            </div>
          </div>

          <input ref={socialInputRef} type="file" accept=".xlsx,.xls" multiple hidden onChange={handleSocialFilesSelected} />
          <input ref={housingInputRef} type="file" accept=".xlsx,.xls" multiple hidden onChange={handleHousingFilesSelected} />
          <input ref={employeeInputRef} type="file" accept=".csv,.xlsx,.xlsm" hidden onChange={handleEmployeeMasterSelected} />

          <div className="upload-board">
            <UploadPanel
              eyebrow={TEXT.socialEyebrow}
              title={TEXT.socialTitle}
              entries={socialEntries}
              onAdd={() => socialInputRef.current?.click()}
              onClear={() => setSocialFiles([])}
              onRemove={removeSocialFile}
              emptyMessage={TEXT.noSocial}
              tone="social"
              disabled={lockSelection}
            />
            <UploadPanel
              eyebrow={TEXT.housingEyebrow}
              title={TEXT.housingTitle}
              entries={housingEntries}
              onAdd={() => housingInputRef.current?.click()}
              onClear={() => setHousingFundFiles([])}
              onRemove={removeHousingFile}
              emptyMessage={TEXT.noHousing}
              tone="housing"
              disabled={lockSelection}
            />
          </div>

          <div className="upload-support-grid">
            <article className="upload-panel upload-panel--master">
              <div className="upload-panel__header upload-panel__header--aligned">
                <div>
                  <span className="panel-label">{TEXT.employeeEyebrow}</span>
                  <h3>{TEXT.employeeTitle}</h3>
                </div>
              </div>
              <label className="form-field form-field--compact">
                <span>{TEXT.employeeMode}</span>
                <select
                  value={effectiveEmployeeMasterMode}
                  onChange={(event) => {
                    const nextMode = event.target.value as 'none' | 'upload' | 'existing';
                    setEmployeeMasterMode(nextMode);
                    if (nextMode !== 'upload') {
                      setEmployeeMasterFile(null);
                    }
                    setSelectionError(null);
                  }}
                  disabled={lockSelection}
                >
                  <option value="none">{TEXT.employeeModeNone}</option>
                  <option value="existing" disabled={loadingEmployeeMasters || existingEmployeeMasterCount <= 0}>
                    {TEXT.employeeModeExisting}
                  </option>
                  <option value="upload">{TEXT.employeeModeUpload}</option>
                </select>
              </label>
              {effectiveEmployeeMasterMode === 'upload' ? (
                <>
                  <div className="upload-panel__actions button-row">
                    <button type="button" className="button button--primary" onClick={() => employeeInputRef.current?.click()} disabled={lockSelection}>
                      {employeeMasterFile ? TEXT.replaceMaster : TEXT.addMaster}
                    </button>
                    <button
                      type="button"
                      className="button button--ghost"
                      disabled={lockSelection || !employeeDisplayName}
                      onClick={() => setEmployeeMasterFile(null)}
                    >
                      {TEXT.removeMaster}
                    </button>
                  </div>
                  {employeeDisplayName ? (
                    <div className="upload-file-chip upload-file-chip--single">
                      <div className="upload-file-chip__meta">
                        <strong>{employeeDisplayName}</strong>
                        <span>{employeeMasterFile ? formatFileSize(employeeMasterFile.size) : TEXT.persistedRecord}</span>
                      </div>
                    </div>
                  ) : (
                    <div className="upload-panel__empty">{TEXT.noEmployee}</div>
                  )}
                </>
              ) : effectiveEmployeeMasterMode === 'existing' ? (
                <div className="upload-file-chip upload-file-chip--single">
                  <div className="upload-file-chip__meta">
                    <strong>
                      {loadingEmployeeMasters
                        ? TEXT.employeeExistingLoading
                        : existingEmployeeMasterCount > 0
                          ? `${existingEmployeeMasterCount} 条在职员工主档`
                          : TEXT.employeeExistingEmpty}
                    </strong>
                    <span>{existingEmployeeMasterCount > 0 ? TEXT.employeeExistingReady : TEXT.employeeExistingEmpty}</span>
                  </div>
                </div>
              ) : (
                <div className="upload-panel__empty">{TEXT.employeeNoneMessage}</div>
              )}
            </article>

            <article className="upload-panel upload-panel--meta">
              <div className="upload-panel__header upload-panel__header--aligned">
                <div>
                  <span className="panel-label">{TEXT.stepOne}</span>
                  <h3>{TEXT.metaTitle}</h3>
                </div>
              </div>
              <label className="form-field form-field--compact">
                <span>{TEXT.batchName}</span>
                <input
                  value={hasSessionRecord && !batchName ? aggregateSession.selection.batchName : batchName}
                  onChange={(event) => setBatchName(event.target.value)}
                  placeholder={TEXT.batchPlaceholder}
                  disabled={lockSelection}
                />
              </label>
              <div className="upload-meta-tip">{TEXT.batchTip}</div>
              <div className="upload-meta-note">{TEXT.employeeHint}</div>
            </article>
          </div>
        </section>

        <section className="panel-card simple-aggregate-card">
          <div className="section-heading">
            <div>
              <span className="panel-label">{TEXT.stepTwo}</span>
              <h2>{TEXT.results}</h2>
            </div>
          </div>
          {running && progress ? (
            <div className="simple-result-stack progress-card progress-card--active">
              <div className="progress-card__summary">
                <div className="loading-pill" aria-hidden="true">
                  <span className="loading-pill__core" />
                </div>
                <div>
                  <strong>{progress.percent}%</strong>
                  <span>{progress.label}</span>
                  <p>{progress.message}</p>
                </div>
              </div>
              <div className="progress-bar progress-bar--active" aria-hidden="true">
                <div className="progress-bar__track">
                  <div className="progress-bar__fill" style={{ width: `${progress.percent}%` }} />
                </div>
              </div>
              {progress.batch_name ? (
                <div className="progress-card__meta status-item">
                  <strong>{progress.batch_name}</strong>
                  <div>{progress.batch_id ?? TEXT.batchIdPending}</div>
                </div>
              ) : null}
              <div className="progress-step-list">
                {PROGRESS_STEPS.map((step) => {
                  const stepState = getStepState(step.key, progress);
                  return (
                    <div key={step.key} className={`progress-step progress-step--${stepState}`}>
                      <strong>{step.label}</strong>
                      <span>{stepState === 'done' ? TEXT.done : stepState === 'active' ? TEXT.active : TEXT.pending}</span>
                    </div>
                  );
                })}
              </div>
              {progress.stage === 'parse' && parseSummary ? (
                <div className="parse-visualizer">
                  <div className="parse-visualizer__header">
                    <strong>{TEXT.parseOverview}</strong>
                    <span>{`实时刷新 ${parseSummary.saved_count}/${parseSummary.total_files}`}</span>
                  </div>
                  <div className="parse-active-panel">
                    <div className="parse-active-panel__header">
                      <strong>{`${TEXT.activeParallel} (${activeParseFiles.length}/${parseSummary.worker_count})`}</strong>
                    </div>
                    {activeParseFiles.length ? (
                      <div className="parse-active-list">
                        {activeParseFiles.map((item) => (
                          <article key={item.source_file_id ?? `${item.file_index}_${item.file_name}_active`} className="parse-active-item">
                            <strong>{item.file_name}</strong>
                            <span>{`${sourceKindLabel(item.source_kind ?? 'social_security')} / ${item.region ?? TEXT.unknownRegion} / ${item.company_name ?? TEXT.unknownCompany}`}</span>
                          </article>
                        ))}
                      </div>
                    ) : (
                      <div className="parse-active-empty">{TEXT.activeIdle}</div>
                    )}
                  </div>
                  <div className="parse-visualizer__summary">
                    <article className="parse-visualizer__metric">
                      <strong>{parseSummary.total_files}</strong>
                      <span>{TEXT.parseTotalFiles}</span>
                    </article>
                    <article className="parse-visualizer__metric">
                      <strong>{parseSummary.worker_count}</strong>
                      <span>{TEXT.parseWorkers}</span>
                    </article>
                    <article className="parse-visualizer__metric">
                      <strong>{parseSummary.queued_count}</strong>
                      <span>{TEXT.parseQueued}</span>
                    </article>
                    <article className="parse-visualizer__metric">
                      <strong>{parseSummary.active_count}</strong>
                      <span>{TEXT.parseRunning}</span>
                    </article>
                    <article className="parse-visualizer__metric">
                      <strong>{Math.max(0, parseSummary.analyzed_count - parseSummary.saved_count)}</strong>
                      <span>{TEXT.parseAnalyzed}</span>
                    </article>
                    <article className="parse-visualizer__metric">
                      <strong>{parseSummary.saved_count}</strong>
                      <span>{TEXT.parseSaved}</span>
                    </article>
                  </div>
                  <div className="parse-file-list">
                    {parseFiles.map((item) => (
                      <article key={item.source_file_id ?? `${item.file_index}_${item.file_name}`} className="parse-file-item">
                        <div className="parse-file-item__title">
                          <strong>{`${item.file_index}. ${item.file_name}`}</strong>
                          <span className={`parse-file-pill parse-file-pill--${parsePhaseTone(item.phase)}`}>{parsePhaseLabel(item.phase)}</span>
                        </div>
                        <div className="parse-file-item__meta">{formatParseFileMeta(item)}</div>
                        {item.raw_sheet_name ? <div className="parse-file-item__sheet">{`${TEXT.parseSheet}：${item.raw_sheet_name}`}</div> : null}
                      </article>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : result ? (
            <div className="simple-result-stack">
              <div className="simple-result-summary status-grid">
                <article className="status-item">
                  <strong>{statusLabel(result.export_status)}</strong>
                  <div>{TEXT.exportStatus}</div>
                </article>
                <article className="status-item">
                  <strong>{normalizedCount}</strong>
                  <div>{TEXT.normalizedCount}</div>
                </article>
                <article className="status-item">
                  <strong>{filteredCount}</strong>
                  <div>{TEXT.filteredCount}</div>
                </article>
                <article className="status-item">
                  <strong>{result.matched_count}</strong>
                  <div>{TEXT.matchedCount}</div>
                </article>
              </div>
              <div className="simple-artifact-list">
                {outputArtifacts.map((artifact) => (
                  <article key={artifact.template_type} className={`simple-artifact-card simple-artifact-card--${artifactTone(artifact)}`}>
                    <div className="simple-artifact-card__body">
                      <strong>{artifactLabel(artifact.template_type)}</strong>
                      <span>{formatArtifactMessage(artifact)}</span>
                    </div>
                    <div className="simple-artifact-card__actions">
                      {artifact.status === 'completed' && result.batch_id ? (
                        <button
                          type="button"
                          className="button button--ghost button--download"
                          onClick={() => void handleDownloadArtifact(artifact.template_type)}
                          disabled={downloadingTemplate === artifact.template_type}
                        >
                          {downloadingTemplate === artifact.template_type ? '下载中...' : TEXT.download}
                        </button>
                      ) : (
                        <span className="simple-artifact-card__status">{artifact.status}</span>
                      )}
                    </div>
                  </article>
                ))}
              </div>
              <div className="simple-source-list">
                {result.source_files.map((file) => (
                  <div key={file.source_file_id} className="status-item">
                    <strong>{`${sourceKindLabel(file.source_kind)} | ${file.file_name}`}</strong>
                    <div>{`${file.region ?? TEXT.unknownRegion} / ${file.company_name ?? TEXT.unknownCompany} / ${file.normalized_record_count} 条明细 / 过滤 ${file.filtered_row_count} 行`}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <SectionState title={TEXT.waitingTitle} message={TEXT.waitingMessage} />
          )}
        </section>
      </div>
    </PageContainer>
  );
}
