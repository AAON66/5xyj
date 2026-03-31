import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Row,
  Select,
  Skeleton,
  Statistic,
  Table,
  Tag,
  Typography,
} from 'antd';
import { ExportOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

import {
  exportBatch,
  fetchBatchExport,
  fetchRuntimeBatches,
  type BatchExport,
  type ExportArtifact,
} from '../services/runtime';

const { Title, Text } = Typography;

const TEMPLATE_ORDER = ['salary', 'final_tool'];

function formatDateTime(value: string | null): string {
  if (!value) return '未完成';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

function exportStatusLabel(value: string | null): string {
  switch (value) {
    case 'completed': return '已完成';
    case 'failed': return '失败';
    case 'blocked': return '已阻塞';
    case 'running': return '导出中';
    case 'pending': return '待执行';
    default: return value ?? '未开始';
  }
}

function artifactStatusLabel(value: string): string {
  switch (value) {
    case 'completed': return '已导出';
    case 'failed': return '导出失败';
    case 'blocked': return '未满足条件';
    case 'missing_template': return '模板缺失';
    case 'pending': return '待生成';
    default: return value;
  }
}

function artifactStatusColor(value: string): string {
  switch (value) {
    case 'completed': return 'success';
    case 'failed': return 'error';
    case 'blocked':
    case 'missing_template': return 'warning';
    default: return 'default';
  }
}

function templateLabel(value: string): string {
  switch (value) {
    case 'salary': return '薪酬模板';
    case 'final_tool': return '工具表最终版';
    default: return value;
  }
}

function sortArtifacts(artifacts: ExportArtifact[]): ExportArtifact[] {
  return [...artifacts].sort((left, right) => {
    const leftIndex = TEMPLATE_ORDER.indexOf(left.template_type);
    const rightIndex = TEMPLATE_ORDER.indexOf(right.template_type);
    return (leftIndex === -1 ? Number.MAX_SAFE_INTEGER : leftIndex) - (rightIndex === -1 ? Number.MAX_SAFE_INTEGER : rightIndex);
  });
}

export function ExportsPage() {
  const [batches, setBatches] = useState<Array<{ id: string; batch_name: string; status: string; updated_at: string }>>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
  const [exportResult, setExportResult] = useState<BatchExport | null>(null);
  const [loading, setLoading] = useState(true);
  const [runningExport, setRunningExport] = useState(false);
  const [notice, setNotice] = useState<{ type: 'success' | 'warning'; message: string } | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function loadBatches() {
      try {
        const result = await fetchRuntimeBatches();
        if (!active) return;
        setBatches(result);
        setPageError(null);
        if (result[0]) {
          setSelectedBatchId((current) => current ?? result[0].id);
        }
      } catch {
        if (active) setPageError('导出页面暂时无法读取批次列表。');
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadBatches();
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    async function loadExportState(batchId: string) {
      try {
        const exportData = await fetchBatchExport(batchId).catch(() => null);
        if (!active) return;
        setExportResult(exportData);
      } catch {
        if (active) setPageError('当前批次的导出快照加载失败。');
      }
    }
    if (!selectedBatchId) {
      setExportResult(null);
      return;
    }
    void loadExportState(selectedBatchId);
    return () => { active = false; };
  }, [selectedBatchId]);

  const artifacts = useMemo<ExportArtifact[]>(() => sortArtifacts(exportResult?.artifacts ?? []), [exportResult]);

  async function refreshBatches(keepId?: string) {
    const result = await fetchRuntimeBatches();
    setBatches(result);
    if (keepId) setSelectedBatchId(keepId);
  }

  async function handleExport() {
    if (!selectedBatchId) return;
    setRunningExport(true);
    setNotice(null);
    try {
      const result = await exportBatch(selectedBatchId);
      setExportResult(result);
      setNotice({
        type: result.blocked_reason ? 'warning' : 'success',
        message: result.blocked_reason ?? `${result.batch_name} 的双模板导出已执行。`,
      });
      await refreshBatches(selectedBatchId);
    } finally {
      setRunningExport(false);
    }
  }

  const artifactColumns: ColumnsType<ExportArtifact> = [
    {
      title: '模板类型',
      dataIndex: 'template_type',
      key: 'template_type',
      render: (val: string) => templateLabel(val),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (val: string) => <Tag color={artifactStatusColor(val)}>{artifactStatusLabel(val)}</Tag>,
    },
    {
      title: '导出行数',
      dataIndex: 'row_count',
      key: 'row_count',
      align: 'right',
    },
    {
      title: '文件路径',
      dataIndex: 'file_path',
      key: 'file_path',
      render: (val: string | null) => val ?? '尚未生成',
      ellipsis: true,
    },
    {
      title: '错误信息',
      dataIndex: 'error_message',
      key: 'error_message',
      render: (val: string | null) => val ? <Text type="danger">{val}</Text> : '-',
    },
  ];

  return (
    <div>
      <Title level={4}>导出结果</Title>

      {notice && (
        <Alert
          type={notice.type}
          message={notice.message}
          closable
          onClose={() => setNotice(null)}
          style={{ marginBottom: 16 }}
        />
      )}
      {pageError && (
        <Alert type="error" message="页面状态异常" description={pageError} style={{ marginBottom: 16 }} />
      )}

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} md={8}>
          <Card title="批次选择">
            {loading ? (
              <Skeleton active paragraph={{ rows: 2 }} />
            ) : (
              <>
                <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                  {batches.length} 个可用批次
                </Text>
                <Select
                  style={{ width: '100%' }}
                  placeholder="请选择批次"
                  value={selectedBatchId}
                  onChange={(val) => setSelectedBatchId(val)}
                  options={batches.map((b) => ({
                    value: b.id,
                    label: `${b.batch_name} (${b.status})`,
                  }))}
                />
                <div style={{ marginTop: 12 }}>
                  <Button
                    type="primary"
                    icon={<ExportOutlined />}
                    onClick={() => void handleExport()}
                    disabled={!selectedBatchId || runningExport}
                    loading={runningExport}
                  >
                    执行双模板导出
                  </Button>
                </div>
              </>
            )}
          </Card>
        </Col>
        <Col xs={24} md={16}>
          <Card>
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Statistic
                  title="导出状态"
                  value={exportStatusLabel(exportResult?.export_status ?? exportResult?.status ?? null)}
                />
              </Col>
              <Col span={6}>
                <Statistic title="模板产物数" value={artifacts.length} />
              </Col>
              <Col span={6}>
                <Statistic
                  title="成功模板数"
                  value={artifacts.filter((item) => item.status === 'completed').length}
                  valueStyle={{ color: '#00B42A' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="累计导出行数"
                  value={artifacts.reduce((sum, item) => sum + item.row_count, 0)}
                />
              </Col>
            </Row>
            <div style={{ marginTop: 12 }}>
              <Text strong>运行说明: </Text>
              <Text type="secondary">
                {exportResult?.blocked_reason ?? '系统会同时检查两份模板，只要任意一份失败，整体状态就会标记为失败。'}
              </Text>
            </div>
            <div style={{ marginTop: 4 }}>
              <Text strong>完成时间: </Text>
              <Text type="secondary">{formatDateTime(exportResult?.completed_at ?? null)}</Text>
            </div>
          </Card>
        </Col>
      </Row>

      <Card title="双模板执行结果">
        {artifacts.length > 0 ? (
          <Table
            size="small"
            columns={artifactColumns}
            dataSource={artifacts}
            rowKey="template_type"
            pagination={false}
          />
        ) : (
          <Empty description="当前批次还没有导出记录。完成匹配后即可在这里触发双模板导出。" />
        )}
      </Card>
    </div>
  );
}
