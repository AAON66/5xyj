import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { PageContainer, SectionState, SurfaceNotice } from '../components';
import { normalizeApiError } from '../services/api';
import {
  runSimpleAggregateWithProgress,
  type AggregateArtifact,
  type AggregateProgressEvent,
  type AggregateRunResult,
} from '../services/aggregate';
import { fetchSystemHealth, type SystemHealth } from '../services/system';

const PROGRESS_STEPS = [
  { key: 'employee_import', label: '员工主档' },
  { key: 'batch_upload', label: '上传批次' },
  { key: 'parse', label: '解析识别' },
  { key: 'validate', label: '数据校验' },
  { key: 'match', label: '工号匹配' },
  { key: 'export', label: '双模板导出' },
] as const;

function artifactLabel(value: string): string {
  return value === 'salary' ? '薪酬模板' : '工具表最终版';
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

function artifactTone(artifact: AggregateArtifact): 'success' | 'warning' | 'error' {
  if (artifact.status === 'completed') {
    return 'success';
  }
  if (artifact.status === 'failed') {
    return 'error';
  }
  return 'warning';
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
  if (targetIndex === currentIndex) {
    return 'active';
  }
  return 'pending';
}

export function SimpleAggregatePage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [socialFiles, setSocialFiles] = useState<File[]>([]);
  const [employeeMasterFile, setEmployeeMasterFile] = useState<File | null>(null);
  const [batchName, setBatchName] = useState('');
  const [running, setRunning] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);
  const [result, setResult] = useState<AggregateRunResult | null>(null);
  const [progress, setProgress] = useState<AggregateProgressEvent | null>(null);

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

  const outputArtifacts = useMemo(() => result?.artifacts ?? [], [result]);
  const normalizedCount = useMemo(
    () => result?.source_files.reduce((sum, item) => sum + item.normalized_record_count, 0) ?? 0,
    [result],
  );
  const filteredCount = useMemo(
    () => result?.source_files.reduce((sum, item) => sum + item.filtered_row_count, 0) ?? 0,
    [result],
  );

  async function handleRun() {
    if (!socialFiles.length) {
      setPageError('请先选择至少一个社保 Excel 文件。');
      return;
    }

    setRunning(true);
    setPageError(null);
    setResult(null);
    setProgress({
      stage: 'employee_import',
      label: '准备开始',
      message: '正在准备快速聚合任务。',
      percent: 0,
    });

    try {
      const payload = await runSimpleAggregateWithProgress({
        files: socialFiles,
        employeeMasterFile,
        batchName,
        onProgress: (event) => setProgress(event),
      });
      setResult(payload);
      setProgress((current) =>
        current ?? {
          stage: 'export',
          label: '导出完成',
          message: '双模板导出流程已结束。',
          percent: 100,
          batch_id: payload.batch_id,
          batch_name: payload.batch_name,
        },
      );
    } catch (error) {
      setPageError(normalizeApiError(error).message || '快速聚合失败，请检查文件内容后重试。');
    } finally {
      setRunning(false);
    }
  }

  return (
    <PageContainer
      eyebrow="Quick Aggregate"
      title="上传后直接导出两份结果"
      description="默认走完整主链路：自动识别表头、过滤非明细行、执行校验和工号匹配，最后同时输出薪酬模板和工具表最终版。"
      actions={
        <div className="button-row">
          <button
            type="button"
            className="button button--primary"
            disabled={!socialFiles.length || running}
            onClick={() => void handleRun()}
          >
            {running ? '正在聚合...' : '开始聚合并导出'}
          </button>
          <Link to="/imports" className="button button--ghost">
            进入高级页面
          </Link>
        </div>
      }
    >
      {health ? (
        <SurfaceNotice
          tone="success"
          title="后端已就绪"
          message={`${health.app_name} ${health.version} | /api/v1/system/health 响应正常`}
        />
      ) : null}
      {pageError ? <SurfaceNotice tone="error" title="本次聚合失败" message={pageError} /> : null}
      {result && result.export_status === 'completed' ? (
        <SurfaceNotice
          tone="success"
          title="两份文件已生成"
          message={`批次 ${result.batch_name} 已完成双模板导出。`}
        />
      ) : null}
      {result && result.employee_master ? (
        <SurfaceNotice
          tone="info"
          title="已同步导入员工主档"
          message={`${result.employee_master.file_name} | 新增 ${result.employee_master.created_count} | 更新 ${result.employee_master.updated_count}`}
        />
      ) : null}
      {result && result.blocked_reason ? (
        <SurfaceNotice tone="warning" title="链路已继续但需关注" message={result.blocked_reason} />
      ) : null}

      <div className="panel-grid panel-grid--two simple-aggregate-grid">
        <section className="panel-card simple-aggregate-card">
          <div className="section-heading">
            <div>
              <span className="panel-label">步骤 1</span>
              <h2>选择文件</h2>
            </div>
          </div>
          <label className="form-field">
            <span>社保明细文件</span>
            <input
              type="file"
              accept=".xlsx,.xls"
              multiple
              onChange={(event) => setSocialFiles(Array.from(event.target.files ?? []))}
            />
          </label>
          <label className="form-field">
            <span>员工主档（可选）</span>
            <input
              type="file"
              accept=".csv,.xlsx,.xlsm"
              onChange={(event) => setEmployeeMasterFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <label className="form-field">
            <span>批次名称（可选）</span>
            <input
              value={batchName}
              onChange={(event) => setBatchName(event.target.value)}
              placeholder="例：2026-02 社保聚合"
            />
          </label>
          <div className="simple-file-list">
            <div className="status-item">
              <strong>{socialFiles.length ? `已选 ${socialFiles.length} 个文件` : '还没有选择文件'}</strong>
              <div>{socialFiles.map((file) => file.name).join(' / ') || '支持同时上传多个 Excel，系统会一起处理。'}</div>
            </div>
            <div className="status-item">
              <strong>{employeeMasterFile ? employeeMasterFile.name : '未附带员工主档'}</strong>
              <div>{employeeMasterFile ? '本次会在聚合前先导入员工主档。' : '不传也可继续导出，但工号会保留空值。'}</div>
            </div>
          </div>
        </section>

        <section className="panel-card simple-aggregate-card">
          <div className="section-heading">
            <div>
              <span className="panel-label">步骤 2</span>
              <h2>直接查看结果</h2>
            </div>
          </div>
          {running && progress ? (
            <div className="simple-result-stack progress-card">
              <div className="progress-card__summary">
                <strong>{progress.percent}%</strong>
                <div>
                  <span>{progress.label}</span>
                  <p>{progress.message}</p>
                </div>
              </div>
              <div className="progress-bar" aria-hidden="true">
                <div className="progress-bar__track">
                  <div className="progress-bar__fill" style={{ width: `${progress.percent}%` }} />
                </div>
              </div>
              {progress.batch_name ? (
                <div className="progress-card__meta status-item">
                  <strong>{progress.batch_name}</strong>
                  <div>{progress.batch_id ?? '批次编号生成中'}</div>
                </div>
              ) : null}
              <div className="progress-step-list">
                {PROGRESS_STEPS.map((step) => {
                  const stepState = getStepState(step.key, progress);
                  return (
                    <div key={step.key} className={`progress-step progress-step--${stepState}`}>
                      <strong>{step.label}</strong>
                      <span>
                        {stepState === 'done' ? '已完成' : stepState === 'active' ? '进行中' : '等待中'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : result ? (
            <div className="simple-result-stack">
              <div className="simple-result-summary status-grid">
                <article className="status-item">
                  <strong>{statusLabel(result.export_status)}</strong>
                  <div>导出状态</div>
                </article>
                <article className="status-item">
                  <strong>{normalizedCount}</strong>
                  <div>聚合后记录数</div>
                </article>
                <article className="status-item">
                  <strong>{filteredCount}</strong>
                  <div>已过滤非明细行</div>
                </article>
                <article className="status-item">
                  <strong>{result.matched_count}</strong>
                  <div>匹配成功记录</div>
                </article>
              </div>
              <div className="simple-artifact-list">
                {outputArtifacts.map((artifact) => (
                  <SurfaceNotice
                    key={artifact.template_type}
                    tone={artifactTone(artifact)}
                    title={artifactLabel(artifact.template_type)}
                    message={formatArtifactMessage(artifact)}
                  />
                ))}
              </div>
              <div className="simple-source-list">
                {result.source_files.map((file) => (
                  <div key={file.source_file_id} className="status-item">
                    <strong>{file.file_name}</strong>
                    <div>
                      {`${file.region ?? '未识别地区'} / ${file.company_name ?? '未识别公司'} / ${file.normalized_record_count} 条明细 / 过滤 ${file.filtered_row_count} 行`}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <SectionState title="等你开始聚合" message="上传社保文件后，这里会直接给你两份导出文件的生成结果和路径。" />
          )}
        </section>
      </div>
    </PageContainer>
  );
}
