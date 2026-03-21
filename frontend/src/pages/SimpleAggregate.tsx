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
  { key: 'employee_import', label: '\u5458\u5de5\u4e3b\u6863' },
  { key: 'batch_upload', label: '\u4e0a\u4f20\u6279\u6b21' },
  { key: 'parse', label: '\u89e3\u6790\u8bc6\u522b' },
  { key: 'validate', label: '\u6570\u636e\u6821\u9a8c' },
  { key: 'match', label: '\u5de5\u53f7\u5339\u914d' },
  { key: 'export', label: '\u53cc\u6a21\u677f\u5bfc\u51fa' },
] as const;

function artifactLabel(value: string): string {
  return value === 'salary' ? '\u85aa\u916c\u6a21\u677f' : '\u5de5\u5177\u8868\u6700\u7ec8\u7248';
}

function statusLabel(value: string | null): string {
  switch (value) {
    case 'completed':
    case 'exported':
      return '\u5df2\u5b8c\u6210';
    case 'failed':
      return '\u5df2\u5931\u8d25';
    case 'matched':
      return '\u5df2\u5339\u914d';
    case 'validated':
      return '\u5df2\u6821\u9a8c';
    case 'normalized':
      return '\u5df2\u6807\u51c6\u5316';
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
  const path = artifact.file_path ?? artifact.error_message ?? '\u6682\u65e0\u8f93\u51fa\u8def\u5f84';
  if (artifact.row_count > 0 && artifact.file_path) {
    return `${path} | ${artifact.row_count} \u884c`;
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

function sourceKindLabel(value: string): string {
  return value === 'housing_fund' ? '\u516c\u79ef\u91d1' : '\u793e\u4fdd';
}

export function SimpleAggregatePage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [socialFiles, setSocialFiles] = useState<File[]>([]);
  const [housingFundFiles, setHousingFundFiles] = useState<File[]>([]);
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
    if (!socialFiles.length && !housingFundFiles.length) {
      setPageError('\u8bf7\u81f3\u5c11\u9009\u62e9\u4e00\u4e2a\u793e\u4fdd\u6216\u516c\u79ef\u91d1 Excel \u6587\u4ef6\u3002');
      return;
    }

    setRunning(true);
    setPageError(null);
    setResult(null);
    setProgress({
      stage: 'employee_import',
      label: '\u51c6\u5907\u5f00\u59cb',
      message: '\u6b63\u5728\u51c6\u5907\u5feb\u901f\u805a\u5408\u4efb\u52a1\u3002',
      percent: 0,
    });

    try {
      const payload = await runSimpleAggregateWithProgress({
        files: socialFiles,
        housingFundFiles,
        employeeMasterFile,
        batchName,
        onProgress: (event) => setProgress(event),
      });
      setResult(payload);
      setProgress((current) =>
        current ?? {
          stage: 'export',
          label: '\u5bfc\u51fa\u5b8c\u6210',
          message: '\u53cc\u6a21\u677f\u5bfc\u51fa\u6d41\u7a0b\u5df2\u7ed3\u675f\u3002',
          percent: 100,
          batch_id: payload.batch_id,
          batch_name: payload.batch_name,
        },
      );
    } catch (error) {
      setPageError(normalizeApiError(error).message || '\u5feb\u901f\u805a\u5408\u5931\u8d25\uff0c\u8bf7\u68c0\u67e5\u6587\u4ef6\u5185\u5bb9\u540e\u91cd\u8bd5\u3002');
    } finally {
      setRunning(false);
    }
  }

  return (
    <PageContainer
      eyebrow="Quick Aggregate"
      title="\u4e0a\u4f20\u540e\u76f4\u63a5\u5bfc\u51fa\u4e24\u4efd\u7ed3\u679c"
      description="\u9ed8\u8ba4\u8d70\u5b8c\u6574\u4e3b\u94fe\u8def\uff1a\u81ea\u52a8\u8bc6\u522b\u793e\u4fdd\u4e0e\u516c\u79ef\u91d1\u8868\u5934\u3001\u8fc7\u6ee4\u975e\u660e\u7ec6\u884c\u3001\u6267\u884c\u6821\u9a8c\u548c\u5de5\u53f7\u5339\u914d\uff0c\u6700\u540e\u540c\u65f6\u8f93\u51fa\u85aa\u916c\u6a21\u677f\u548c\u5de5\u5177\u8868\u6700\u7ec8\u7248\u3002"
      actions={
        <div className="button-row">
          <button
            type="button"
            className="button button--primary"
            disabled={(!socialFiles.length && !housingFundFiles.length) || running}
            onClick={() => void handleRun()}
          >
            {running ? '\u6b63\u5728\u805a\u5408...' : '\u5f00\u59cb\u805a\u5408\u5e76\u5bfc\u51fa'}
          </button>
          <Link to="/imports" className="button button--ghost">
            \u8fdb\u5165\u9ad8\u7ea7\u9875\u9762
          </Link>
        </div>
      }
    >
      {health ? (
        <SurfaceNotice
          tone="success"
          title="\u540e\u7aef\u5df2\u5c31\u7eea"
          message={`${health.app_name} ${health.version} | /api/v1/system/health \u54cd\u5e94\u6b63\u5e38`}
        />
      ) : null}
      {pageError ? <SurfaceNotice tone="error" title="\u672c\u6b21\u805a\u5408\u5931\u8d25" message={pageError} /> : null}
      {result && result.export_status === 'completed' ? (
        <SurfaceNotice
          tone="success"
          title="\u4e24\u4efd\u6587\u4ef6\u5df2\u751f\u6210"
          message={`\u6279\u6b21 ${result.batch_name} \u5df2\u5b8c\u6210\u53cc\u6a21\u677f\u5bfc\u51fa\u3002`}
        />
      ) : null}
      {result && result.employee_master ? (
        <SurfaceNotice
          tone="info"
          title="\u5df2\u540c\u6b65\u5bfc\u5165\u5458\u5de5\u4e3b\u6863"
          message={`${result.employee_master.file_name} | \u65b0\u589e ${result.employee_master.created_count} | \u66f4\u65b0 ${result.employee_master.updated_count}`}
        />
      ) : null}
      {result && result.blocked_reason ? (
        <SurfaceNotice tone="warning" title="\u94fe\u8def\u5df2\u7ee7\u7eed\u4f46\u9700\u5173\u6ce8" message={result.blocked_reason} />
      ) : null}

      <div className="panel-grid panel-grid--two simple-aggregate-grid">
        <section className="panel-card simple-aggregate-card">
          <div className="section-heading">
            <div>
              <span className="panel-label">\u6b65\u9aa4 1</span>
              <h2>\u9009\u62e9\u6587\u4ef6</h2>
            </div>
          </div>
          <label className="form-field">
            <span>\u793e\u4fdd\u660e\u7ec6\u6587\u4ef6</span>
            <input
              type="file"
              accept=".xlsx,.xls"
              multiple
              onChange={(event) => setSocialFiles(Array.from(event.target.files ?? []))}
            />
          </label>
          <label className="form-field">
            <span>\u516c\u79ef\u91d1\u660e\u7ec6\u6587\u4ef6</span>
            <input
              type="file"
              accept=".xlsx,.xls"
              multiple
              onChange={(event) => setHousingFundFiles(Array.from(event.target.files ?? []))}
            />
          </label>
          <label className="form-field">
            <span>\u5458\u5de5\u4e3b\u6863\uff08\u53ef\u9009\uff09</span>
            <input
              type="file"
              accept=".csv,.xlsx,.xlsm"
              onChange={(event) => setEmployeeMasterFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <label className="form-field">
            <span>\u6279\u6b21\u540d\u79f0\uff08\u53ef\u9009\uff09</span>
            <input
              value={batchName}
              onChange={(event) => setBatchName(event.target.value)}
              placeholder="\u4f8b\uff1a2026-02 \u793e\u4fdd\u516c\u79ef\u91d1\u805a\u5408"
            />
          </label>
          <div className="simple-file-list">
            <div className="status-item">
              <strong>{socialFiles.length ? `\u5df2\u9009 ${socialFiles.length} \u4e2a\u793e\u4fdd\u6587\u4ef6` : '\u8fd8\u6ca1\u6709\u9009\u62e9\u793e\u4fdd\u6587\u4ef6'}</strong>
              <div>{socialFiles.map((file) => file.name).join(' / ') || '\u652f\u6301\u540c\u65f6\u4e0a\u4f20\u591a\u4e2a\u793e\u4fdd Excel\uff0c\u7cfb\u7edf\u4f1a\u4e00\u8d77\u5904\u7406\u3002'}</div>
            </div>
            <div className="status-item">
              <strong>{housingFundFiles.length ? `\u5df2\u9009 ${housingFundFiles.length} \u4e2a\u516c\u79ef\u91d1\u6587\u4ef6` : '\u8fd8\u6ca1\u6709\u9009\u62e9\u516c\u79ef\u91d1\u6587\u4ef6'}</strong>
              <div>{housingFundFiles.map((file) => file.name).join(' / ') || '\u53ef\u4e0e\u793e\u4fdd\u6587\u4ef6\u4e00\u8d77\u4e0a\u4f20\uff0c\u7cfb\u7edf\u4f1a\u81ea\u52a8\u5408\u5e76\u5230\u540c\u4e00\u6279\u6b21\u3002'}</div>
            </div>
            <div className="status-item">
              <strong>{employeeMasterFile ? employeeMasterFile.name : '\u672a\u9644\u5e26\u5458\u5de5\u4e3b\u6863'}</strong>
              <div>{employeeMasterFile ? '\u672c\u6b21\u4f1a\u5728\u805a\u5408\u524d\u5148\u5bfc\u5165\u5458\u5de5\u4e3b\u6863\u3002' : '\u4e0d\u4f20\u4e5f\u53ef\u7ee7\u7eed\u5bfc\u51fa\uff0c\u4f46\u5de5\u53f7\u4f1a\u4fdd\u7559\u7a7a\u503c\u3002'}</div>
            </div>
          </div>
        </section>

        <section className="panel-card simple-aggregate-card">
          <div className="section-heading">
            <div>
              <span className="panel-label">\u6b65\u9aa4 2</span>
              <h2>\u76f4\u63a5\u67e5\u770b\u7ed3\u679c</h2>
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
                  <div>{progress.batch_id ?? '\u6279\u6b21\u7f16\u53f7\u751f\u6210\u4e2d'}</div>
                </div>
              ) : null}
              <div className="progress-step-list">
                {PROGRESS_STEPS.map((step) => {
                  const stepState = getStepState(step.key, progress);
                  return (
                    <div key={step.key} className={`progress-step progress-step--${stepState}`}>
                      <strong>{step.label}</strong>
                      <span>
                        {stepState === 'done' ? '\u5df2\u5b8c\u6210' : stepState === 'active' ? '\u8fdb\u884c\u4e2d' : '\u7b49\u5f85\u4e2d'}
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
                  <div>\u5bfc\u51fa\u72b6\u6001</div>
                </article>
                <article className="status-item">
                  <strong>{normalizedCount}</strong>
                  <div>\u805a\u5408\u540e\u8bb0\u5f55\u6570</div>
                </article>
                <article className="status-item">
                  <strong>{filteredCount}</strong>
                  <div>\u5df2\u8fc7\u6ee4\u975e\u660e\u7ec6\u884c</div>
                </article>
                <article className="status-item">
                  <strong>{result.matched_count}</strong>
                  <div>\u5339\u914d\u6210\u529f\u8bb0\u5f55</div>
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
                    <strong>{`${sourceKindLabel(file.source_kind)} | ${file.file_name}`}</strong>
                    <div>
                      {`${file.region ?? '\u672a\u8bc6\u522b\u5730\u533a'} / ${file.company_name ?? '\u672a\u8bc6\u522b\u516c\u53f8'} / ${file.normalized_record_count} \u6761\u660e\u7ec6 / \u8fc7\u6ee4 ${file.filtered_row_count} \u884c`}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <SectionState title="\u7b49\u4f60\u5f00\u59cb\u805a\u5408" message="\u4e0a\u4f20\u793e\u4fdd\u3001\u516c\u79ef\u91d1\u6587\u4ef6\u540e\uff0c\u8fd9\u91cc\u4f1a\u76f4\u63a5\u7ed9\u4f60\u4e24\u4efd\u5bfc\u51fa\u6587\u4ef6\u7684\u751f\u6210\u7ed3\u679c\u548c\u8def\u5f84\u3002" />
          )}
        </section>
      </div>
    </PageContainer>
  );
}
