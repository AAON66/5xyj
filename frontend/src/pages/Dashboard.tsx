import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Button, Card, Col, Empty, Row, Skeleton, Statistic, Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';

import { fetchDashboardOverview, fetchDataQuality, type DashboardOverview, type DataQualityOverview } from '../services/dashboard';
import { fetchSystemHealth, type SystemHealth } from '../services/system';

const { Title, Text } = Typography;

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

function tagColor(value: string): string {
  if (value === 'failed' || value === 'error' || value === 'blocked') {
    return 'error';
  }
  if (value === 'warning' || value === 'duplicate' || value === 'low_confidence' || value === 'pending') {
    return 'warning';
  }
  return 'success';
}

function healthLabel(health: SystemHealth | null, loading: boolean): string {
  if (loading) return '检测中';
  if (!health) return '未连通';
  return health.status === 'ok' ? '运行正常' : health.status;
}

interface DistributionEntry {
  key: string;
  label: string;
  count: number;
  status: string;
}

function DistributionCard({ title, items }: { title: string; items: Record<string, number> }) {
  const entries: DistributionEntry[] = Object.entries(items).map(([key, count]) => ({
    key,
    label: labelForKey(key),
    count,
    status: key,
  }));

  const columns: ColumnsType<DistributionEntry> = [
    {
      title: '状态',
      dataIndex: 'label',
      key: 'label',
      render: (text: string, record: DistributionEntry) => (
        <Tag color={tagColor(record.status)}>{text}</Tag>
      ),
    },
    {
      title: '数量',
      dataIndex: 'count',
      key: 'count',
      align: 'right',
      sorter: (a: DistributionEntry, b: DistributionEntry) => a.count - b.count,
    },
  ];

  return (
    <Card title={title} size="small">
      {entries.length > 0 ? (
        <Table
          dataSource={entries}
          columns={columns}
          rowKey="key"
          size="small"
          pagination={false}
        />
      ) : (
        <Empty description="暂无数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      )}
    </Card>
  );
}

interface BatchQualityRow {
  batch_id: string;
  batch_name: string;
  record_count: number;
  missing_fields: number;
  anomalous_amounts: number;
  duplicate_records: number;
}

export function DashboardPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [quality, setQuality] = useState<DataQualityOverview | null>(null);
  const [qualityLoading, setQualityLoading] = useState(true);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadDashboard() {
      try {
        const [healthResult, overviewResult] = await Promise.all([
          fetchSystemHealth().catch(() => null),
          fetchDashboardOverview().catch(() => null),
        ]);
        if (!active) return;
        setHealth(healthResult);
        setOverview(overviewResult);
        if (!healthResult && !overviewResult) {
          setPageError('健康检查和看板概览都暂时不可用，请稍后重试。');
        } else {
          setPageError(null);
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    fetchDataQuality()
      .then((data) => { if (active) setQuality(data); })
      .catch(() => {})
      .finally(() => { if (active) setQualityLoading(false); });

    void loadDashboard();
    return () => { active = false; };
  }, []);

  const totalCards = useMemo(() => {
    const totals = overview?.totals;
    return [
      { label: '导入批次', value: totals?.total_batches ?? 0 },
      { label: '源文件', value: totals?.total_source_files ?? 0 },
      { label: '标准化记录', value: totals?.total_normalized_records ?? 0 },
      { label: '校验问题', value: totals?.total_validation_issues ?? 0 },
    ];
  }, [overview]);

  const qualityColumns: ColumnsType<BatchQualityRow> = [
    { title: '批次名称', dataIndex: 'batch_name', key: 'batch_name' },
    { title: '记录数', dataIndex: 'record_count', key: 'record_count', align: 'right', sorter: (a, b) => a.record_count - b.record_count },
    {
      title: '缺失',
      dataIndex: 'missing_fields',
      key: 'missing_fields',
      align: 'right',
      sorter: (a, b) => a.missing_fields - b.missing_fields,
      render: (val: number) => val > 0 ? <Tag color="warning">{val}</Tag> : '0',
    },
    {
      title: '异常',
      dataIndex: 'anomalous_amounts',
      key: 'anomalous_amounts',
      align: 'right',
      sorter: (a, b) => a.anomalous_amounts - b.anomalous_amounts,
      render: (val: number) => val > 0 ? <Tag color="warning">{val}</Tag> : '0',
    },
    {
      title: '重复',
      dataIndex: 'duplicate_records',
      key: 'duplicate_records',
      align: 'right',
      sorter: (a, b) => a.duplicate_records - b.duplicate_records,
      render: (val: number) => val > 0 ? <Tag color="error">{val}</Tag> : '0',
    },
  ];

  const recentBatchColumns: ColumnsType<NonNullable<DashboardOverview['recent_batches']>[number]> = [
    {
      title: '批次名称',
      dataIndex: 'batch_name',
      key: 'batch_name',
      render: (text: string, record) => <Link to={`/imports/${record.batch_id}`}>{text}</Link>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (val: string) => <Tag color={tagColor(val)}>{labelForKey(val)}</Tag>,
    },
    { title: '文件', dataIndex: 'file_count', key: 'file_count', align: 'right' },
    { title: '标准化', dataIndex: 'normalized_record_count', key: 'normalized_record_count', align: 'right' },
    { title: '校验问题', dataIndex: 'validation_issue_count', key: 'validation_issue_count', align: 'right' },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (val: string) => formatDateTime(val),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={4} style={{ margin: 0 }}>处理看板</Title>
          <Text type="secondary">集中查看系统健康、批次体量、运行分布和最近批次进展</Text>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Link to="/imports"><Button type="primary">继续导入与解析</Button></Link>
          <Link to="/exports"><Button>查看导出结果</Button></Link>
        </div>
      </div>

      {pageError && (
        <Card style={{ marginBottom: 16, borderColor: '#F54A45' }}>
          <Text type="danger">{pageError}</Text>
        </Card>
      )}

      {/* Top statistics cards */}
      {loading ? (
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          {[1, 2, 3, 4].map((i) => (
            <Col span={6} key={i}>
              <Card><Skeleton.Input active style={{ width: '100%' }} /></Card>
            </Col>
          ))}
        </Row>
      ) : (
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          {totalCards.map((item, idx) => (
            <Col span={6} key={item.label}>
              <Card>
                <Statistic
                  title={item.label}
                  value={item.value}
                  valueStyle={{ fontSize: 24, color: idx === 0 ? '#3370FF' : undefined }}
                />
              </Card>
            </Col>
          ))}
        </Row>
      )}

      {/* System health card */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Statistic title="系统健康" value={healthLabel(health, loading)} />
          </Col>
          <Col span={8}>
            <Statistic title="概览生成时间" value={overview ? formatDateTime(overview.generated_at) : '尚未生成'} />
          </Col>
          <Col span={8}>
            <Statistic title="匹配结果" value={overview?.totals?.total_match_results ?? 0} />
          </Col>
        </Row>
      </Card>

      {/* Distribution cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <DistributionCard title="批次状态" items={overview?.batch_status_counts ?? {}} />
        </Col>
        <Col span={6}>
          <DistributionCard title="匹配状态" items={overview?.match_status_counts ?? {}} />
        </Col>
        <Col span={6}>
          <DistributionCard title="问题严重级别" items={overview?.issue_severity_counts ?? {}} />
        </Col>
        <Col span={6}>
          <DistributionCard title="导出状态" items={overview?.export_status_counts ?? {}} />
        </Col>
      </Row>

      {/* Data Quality Section */}
      <Title level={5} style={{ marginBottom: 12 }}>导入质量监控</Title>
      {qualityLoading ? (
        <Card><Skeleton active paragraph={{ rows: 5 }} /></Card>
      ) : !quality || (quality.total_missing === 0 && quality.total_anomalous === 0 && quality.total_duplicates === 0 && quality.batches.length === 0) ? (
        <Card><Empty description="暂无质量数据" /></Card>
      ) : (
        <>
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Card>
                <Statistic title="缺失字段" value={quality.total_missing} suffix="条" />
                {quality.total_missing > 0 && <Tag color="warning" style={{ marginTop: 8 }}>需关注</Tag>}
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic title="异常金额" value={quality.total_anomalous} suffix="条" />
                {quality.total_anomalous > 10
                  ? <Tag color="error" style={{ marginTop: 8 }}>严重</Tag>
                  : quality.total_anomalous > 0
                    ? <Tag color="warning" style={{ marginTop: 8 }}>需关注</Tag>
                    : null}
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic title="重复记录" value={quality.total_duplicates} suffix="条" />
                {quality.total_duplicates > 0 && <Tag color="error" style={{ marginTop: 8 }}>需处理</Tag>}
              </Card>
            </Col>
          </Row>
          {quality.batches.length > 0 && (
            <Card title="各批次质量明细" size="small" style={{ marginBottom: 16 }}>
              <Table
                dataSource={quality.batches}
                columns={qualityColumns}
                rowKey="batch_id"
                size="small"
                pagination={false}
              />
            </Card>
          )}
        </>
      )}

      {/* Recent batches */}
      <Card title="最近 5 个批次" size="small">
        {loading ? (
          <Skeleton active paragraph={{ rows: 5 }} />
        ) : overview?.recent_batches.length ? (
          <Table
            dataSource={overview.recent_batches}
            columns={recentBatchColumns}
            rowKey="batch_id"
            size="small"
            pagination={false}
          />
        ) : (
          <Empty description="还没有批次活动记录。先去上传样例并跑通一条批次链路，这里就会自动出现最近进展。" />
        )}
      </Card>
    </div>
  );
}
