import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { PageContainer } from '../components';
import { fetchDashboardOverview, type DashboardOverview } from '../services/dashboard';
import { fetchSystemHealth, type SystemHealth } from '../services/system';

const pipelineSteps = ['导入', '识别', '标准化', '过滤', '匹配', '校验', '双模板导出'];

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

function labelForKey(value: string): string {
  switch (value) {
    case 'uploaded':
      return '已上传';
    case 'parsed':
      return '已解析';
    case 'validated':
      return '已校验';
    case 'matched':
      return '已匹配';
    case 'exported':
      return '已导出';
    case 'failed':
      return '失败';
    case 'blocked':
      return '阻塞';
    case 'unmatched':
      return '未匹配';
    case 'duplicate':
      return '重复命中';
    case 'low_confidence':
      return '低置信度';
    case 'error':
      return '错误';
    case 'warning':
      return '警告';
    case 'info':
      return '提示';
    case 'completed':
      return '已完成';
    case 'pending':
      return '待执行';
    case 'running':
      return '执行中';
    default:
      return value;
  }
}

function healthLabel(health: SystemHealth | null, loading: boolean): string {
  if (loading) {
    return '检测中';
  }
  if (!health) {
    return '未连通';
  }
  return health.status === 'ok' ? '运行正常' : health.status;
}

function statusTone(value: string): string {
  if (value === 'failed' || value === 'error' || value === 'blocked') {
    return 'dashboard-pill--danger';
  }
  if (value === 'warning' || value === 'duplicate' || value === 'low_confidence' || value === 'pending') {
    return 'dashboard-pill--warn';
  }
  return 'dashboard-pill--ok';
}

function DistributionCard({
  title,
  items,
}: {
  title: string;
  items: Record<string, number>;
}) {
  const entries = Object.entries(items);

  return (
    <section className="panel-card panel-card--soft">
      <div className="section-heading">
        <div>
          <span className="panel-label">状态分布</span>
          <h2>{title}</h2>
        </div>
      </div>
      {entries.length > 0 ? (
        <div className="distribution-list">
          {entries.map(([key, count]) => (
            <div key={key} className="distribution-row">
              <span className={`dashboard-pill ${statusTone(key)}`}>{labelForKey(key)}</span>
              <strong>{count}</strong>
            </div>
          ))}
        </div>
      ) : (
        <div className="status-item">当前还没有可展示的数据。</div>
      )}
    </section>
  );
}

export function DashboardPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadDashboard() {
      try {
        const [healthResult, overviewResult] = await Promise.all([
          fetchSystemHealth().catch(() => null),
          fetchDashboardOverview().catch(() => null),
        ]);
        if (!active) {
          return;
        }
        setHealth(healthResult);
        setOverview(overviewResult);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadDashboard();
    return () => {
      active = false;
    };
  }, []);

  const totalCards = useMemo(() => {
    const totals = overview?.totals;
    return [
      { label: '导入批次', value: totals?.total_batches ?? 0, hint: '已写入数据库的批次数量' },
      { label: '源文件', value: totals?.total_source_files ?? 0, hint: '已上传并纳入批次管理的文件数' },
      { label: '标准化记录', value: totals?.total_normalized_records ?? 0, hint: '完成标准化并可进入校验链路的明细行' },
      { label: '校验问题', value: totals?.total_validation_issues ?? 0, hint: '当前累计发现的问题数量' },
      { label: '匹配结果', value: totals?.total_match_results ?? 0, hint: '工号匹配执行后产生的结果条数' },
      { label: '导出任务', value: totals?.total_export_jobs ?? 0, hint: '已触发的双模板导出任务数' },
      { label: '员工主档', value: totals?.active_employee_masters ?? 0, hint: '当前可用于匹配的主档记录数' },
    ];
  }, [overview]);

  return (
    <PageContainer
      eyebrow="Dashboard"
      title="处理链路看板"
      description="集中查看系统健康、批次体量、运行分布和最近批次进展，帮助我们快速判断链路是否通畅以及卡点在哪一环。"
      actions={
        <div className="button-row">
          <Link to="/imports" className="button button--primary">
            继续导入与解析
          </Link>
          <Link to="/exports" className="button button--ghost">
            查看导出结果
          </Link>
        </div>
      }
    >
      <div className="dashboard-hero-grid">
        <section className="panel-card panel-card--accent dashboard-health-card">
          <span className="panel-label">系统健康</span>
          <strong>{healthLabel(health, loading)}</strong>
          <p>
            {loading
              ? '正在同时读取健康检查和看板概览。'
              : health
                ? `${health.app_name} ${health.version} 已可访问，接口层处于可用状态。`
                : '健康检查暂时不可用，但你仍可以从下面的统计卡片判断是否已有历史数据。'}
          </p>
          <div className="dashboard-meta-list">
            <div>
              <span>概览生成时间</span>
              <strong>{overview ? formatDateTime(overview.generated_at) : '尚未生成'}</strong>
            </div>
            <div>
              <span>当前主链路</span>
              <strong>{pipelineSteps.join(' -> ')}</strong>
            </div>
          </div>
        </section>

        <section className="panel-card dashboard-pipeline-card">
          <span className="panel-label">交付原则</span>
          <strong>数据链路优先，规则优先于 LLM</strong>
          <div className="pipeline-chip-list">
            {pipelineSteps.map((step) => (
              <span key={step} className="pipeline-chip">
                {step}
              </span>
            ))}
          </div>
          <p>看板只做状态呈现，不把地区差异硬编码到前端；解析、映射和过滤逻辑仍然收敛在后端服务层。</p>
        </section>
      </div>

      <div className="dashboard-metric-grid">
        {totalCards.map((item) => (
          <article key={item.label} className="panel-card dashboard-metric-card">
            <span className="panel-label">{item.label}</span>
            <strong>{item.value}</strong>
            <p>{item.hint}</p>
          </article>
        ))}
      </div>

      <div className="dashboard-distribution-grid">
        <DistributionCard title="批次状态" items={overview?.batch_status_counts ?? {}} />
        <DistributionCard title="匹配状态" items={overview?.match_status_counts ?? {}} />
        <DistributionCard title="问题严重级别" items={overview?.issue_severity_counts ?? {}} />
        <DistributionCard title="导出状态" items={overview?.export_status_counts ?? {}} />
      </div>

      <section className="panel-card">
        <div className="section-heading">
          <div>
            <span className="panel-label">最近活动</span>
            <h2>最近 5 个批次</h2>
          </div>
        </div>
        {overview?.recent_batches.length ? (
          <div className="recent-batch-grid">
            {overview.recent_batches.map((batch) => (
              <Link key={batch.batch_id} to={`/imports/${batch.batch_id}`} className="recent-batch-card">
                <div className="recent-batch-card__head">
                  <div>
                    <strong>{batch.batch_name}</strong>
                    <p>{formatDateTime(batch.updated_at)}</p>
                  </div>
                  <span className={`dashboard-pill ${statusTone(batch.status)}`}>{labelForKey(batch.status)}</span>
                </div>
                <div className="recent-batch-stats">
                  <div>
                    <span>文件</span>
                    <strong>{batch.file_count}</strong>
                  </div>
                  <div>
                    <span>标准化</span>
                    <strong>{batch.normalized_record_count}</strong>
                  </div>
                  <div>
                    <span>校验问题</span>
                    <strong>{batch.validation_issue_count}</strong>
                  </div>
                  <div>
                    <span>匹配结果</span>
                    <strong>{batch.match_result_count}</strong>
                  </div>
                  <div>
                    <span>导出任务</span>
                    <strong>{batch.export_job_count}</strong>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="status-item">还没有批次活动记录。先去上传样例并跑通一条批次链路，这里就会自动出现最近进展。</div>
        )}
      </section>
    </PageContainer>
  );
}
