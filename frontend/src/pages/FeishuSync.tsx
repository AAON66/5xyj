import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Modal,
  Progress,
  Radio,
  Row,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { CloudSyncOutlined, SyncOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

import { normalizeApiError } from '../services/api';
import {
  fetchSyncConfigs,
  fetchSyncHistory,
  pushToFeishu,
  confirmPush,
  previewPullConflicts,
  executePull,
  readNdjsonStream,
  retrySyncJob,
  type SyncConfig,
  type SyncJob,
  type ConflictPreview,
  type ConflictRecord,
} from '../services/feishu';
import { useFeishuFeatureFlag } from '../hooks/useFeishuFeatureFlag';

const { Title, Text } = Typography;

const STATUS_COLOR: Record<string, string> = {
  success: '#00B42A',
  failed: '#F54A45',
  partial: '#FF7D00',
  running: 'processing',
  pending: 'default',
};

const STATUS_LABEL: Record<string, string> = {
  success: '成功',
  failed: '失败',
  partial: '部分成功',
  running: '运行中',
  pending: '等待中',
};

const DIRECTION_CONFIG: Record<string, { color: string; label: string }> = {
  push: { color: 'blue', label: '推送' },
  pull: { color: 'green', label: '拉取' },
};

export function FeishuSyncPage() {
  const navigate = useNavigate();
  const {
    feishu_sync_enabled,
    feishu_credentials_configured,
    loading: flagsLoading,
  } = useFeishuFeatureFlag();

  const [configs, setConfigs] = useState<SyncConfig[]>([]);
  const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null);
  const [history, setHistory] = useState<SyncJob[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [progress, setProgress] = useState<{
    percent: number;
    processed: number;
    total: number;
  } | null>(null);

  // Push conflict state
  const [pushConflicts, setPushConflicts] = useState<ConflictPreview | null>(null);
  const [pushConflictModalOpen, setPushConflictModalOpen] = useState(false);

  // Pull conflict state
  const [pullConflicts, setPullConflicts] = useState<ConflictPreview | null>(null);
  const [pullConflictModalOpen, setPullConflictModalOpen] = useState(false);
  const [pullStrategy, setPullStrategy] = useState<string>('system_wins');
  const [showDiffOnly, setShowDiffOnly] = useState(true);
  const [perRecordChoices, setPerRecordChoices] = useState<Record<string, string>>({});

  // Redirect when feature is disabled
  useEffect(() => {
    if (!flagsLoading && !feishu_sync_enabled) {
      navigate('/');
    }
  }, [flagsLoading, feishu_sync_enabled, navigate]);

  const loadConfigs = useCallback(async () => {
    try {
      const data = await fetchSyncConfigs();
      setConfigs(data);
    } catch {
      // Silently handle -- configs may not be available yet
    }
  }, []);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const data = await fetchSyncHistory(undefined, 50, 0);
      setHistory(data);
    } catch {
      // Silently handle
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConfigs();
    loadHistory();
  }, [loadConfigs, loadHistory]);

  const configNameMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const c of configs) {
      map.set(c.id, c.name);
    }
    return map;
  }, [configs]);

  // ── Push handler ─────────────────────────────────────────────────

  const handlePush = useCallback(async () => {
    if (!selectedConfigId) return;
    setSyncing(true);
    setProgress(null);

    try {
      const response = await pushToFeishu(selectedConfigId);

      if (!response.ok) {
        const errorText = await response.text();
        message.error(`推送失败: ${errorText}`);
        return;
      }

      const contentType = response.headers.get('content-type') || '';

      if (contentType.includes('application/json')) {
        // Conflict preview response
        const data = await response.json();
        if (data.message === 'conflict_preview' || data.data?.conflicts) {
          const conflicts: ConflictPreview = data.data ?? data;
          setPushConflicts(conflicts);
          setPushConflictModalOpen(true);
          return;
        }
        message.success('推送完成');
      } else {
        // NDJSON stream
        await readNdjsonStream(response, (event) => {
          if (event.type === 'progress') {
            setProgress({
              percent: Number(event.percent ?? 0),
              processed: Number(event.processed ?? 0),
              total: Number(event.total ?? 0),
            });
          }
          if (event.type === 'complete') {
            message.success('同步完成');
          }
          if (event.type === 'error') {
            message.error(String(event.message ?? '同步出错'));
          }
        });
      }

      loadHistory();
    } catch (err) {
      message.error(normalizeApiError(err).message);
    } finally {
      setSyncing(false);
      setProgress(null);
    }
  }, [selectedConfigId, loadHistory]);

  // Push conflict actions
  const handlePushConfirm = useCallback(
    async (action: 'overwrite' | 'skip' | 'cancel') => {
      if (!selectedConfigId) return;
      setPushConflictModalOpen(false);

      if (action === 'cancel') {
        setPushConflicts(null);
        return;
      }

      setSyncing(true);
      try {
        const response = await confirmPush(selectedConfigId, action);
        if (!response.ok) {
          const errorText = await response.text();
          message.error(`操作失败: ${errorText}`);
          return;
        }

        await readNdjsonStream(response, (event) => {
          if (event.type === 'progress') {
            setProgress({
              percent: Number(event.percent ?? 0),
              processed: Number(event.processed ?? 0),
              total: Number(event.total ?? 0),
            });
          }
          if (event.type === 'complete') {
            message.success('推送完成');
          }
          if (event.type === 'error') {
            message.error(String(event.message ?? '推送出错'));
          }
        });
        loadHistory();
      } catch (err) {
        message.error(normalizeApiError(err).message);
      } finally {
        setSyncing(false);
        setProgress(null);
        setPushConflicts(null);
      }
    },
    [selectedConfigId, loadHistory],
  );

  // ── Pull handler ─────────────────────────────────────────────────

  const handlePull = useCallback(async () => {
    if (!selectedConfigId) return;
    setSyncing(true);
    setProgress(null);

    try {
      const preview = await previewPullConflicts(selectedConfigId);

      if (preview.total_conflicts > 0) {
        setPullConflicts(preview);
        setPullConflictModalOpen(true);
        setPullStrategy('system_wins');
        setPerRecordChoices({});
        setSyncing(false);
        return;
      }

      // No conflicts -- directly execute
      const response = await executePull(selectedConfigId, 'system_wins');

      if (!response.ok) {
        const errorText = await response.text();
        message.error(`拉取失败: ${errorText}`);
        return;
      }

      await readNdjsonStream(response, (event) => {
        if (event.type === 'progress') {
          setProgress({
            percent: Number(event.percent ?? 0),
            processed: Number(event.processed ?? 0),
            total: Number(event.total ?? 0),
          });
        }
        if (event.type === 'complete') {
          message.success('拉取完成');
        }
        if (event.type === 'error') {
          message.error(String(event.message ?? '拉取出错'));
        }
      });

      loadHistory();
    } catch (err) {
      message.error(normalizeApiError(err).message);
    } finally {
      setSyncing(false);
      setProgress(null);
    }
  }, [selectedConfigId, loadHistory]);

  // Pull confirm
  const handlePullConfirm = useCallback(async () => {
    if (!selectedConfigId) return;
    setPullConflictModalOpen(false);
    setSyncing(true);

    try {
      const choices = pullStrategy === 'per_record' ? perRecordChoices : undefined;
      const response = await executePull(selectedConfigId, pullStrategy, choices);

      if (!response.ok) {
        const errorText = await response.text();
        message.error(`拉取失败: ${errorText}`);
        return;
      }

      await readNdjsonStream(response, (event) => {
        if (event.type === 'progress') {
          setProgress({
            percent: Number(event.percent ?? 0),
            processed: Number(event.processed ?? 0),
            total: Number(event.total ?? 0),
          });
        }
        if (event.type === 'complete') {
          message.success('拉取完成');
        }
        if (event.type === 'error') {
          message.error(String(event.message ?? '拉取出错'));
        }
      });

      loadHistory();
    } catch (err) {
      message.error(normalizeApiError(err).message);
    } finally {
      setSyncing(false);
      setProgress(null);
      setPullConflicts(null);
    }
  }, [selectedConfigId, pullStrategy, perRecordChoices, loadHistory]);

  const handleRetry = useCallback(
    async (jobId: string) => {
      try {
        await retrySyncJob(jobId);
        message.success('已重新触发同步');
        loadHistory();
      } catch (err) {
        message.error(normalizeApiError(err).message);
      }
    },
    [loadHistory],
  );

  // ── Push conflict columns ────────────────────────────────────────

  const pushConflictColumns: ColumnsType<ConflictRecord> = [
    {
      title: '员工',
      dataIndex: 'person_name',
      key: 'person_name',
      width: 100,
      render: (val: string | null) => val || '-',
    },
    {
      title: '字段',
      dataIndex: 'diff_fields',
      key: 'diff_fields',
      width: 200,
      render: (fields: string[]) => fields.join(', '),
    },
    {
      title: '系统值',
      key: 'system_values',
      width: 200,
      render: (_: unknown, record: ConflictRecord) => (
        <div>
          {record.diff_fields.map((field) => (
            <div
              key={field}
              style={{ background: '#FFF7E6', padding: '2px 4px', marginBottom: 2 }}
            >
              {field}: {String(record.system_values[field] ?? '-')}
            </div>
          ))}
        </div>
      ),
    },
    {
      title: '飞书值',
      key: 'feishu_values',
      width: 200,
      render: (_: unknown, record: ConflictRecord) => (
        <div>
          {record.diff_fields.map((field) => (
            <div
              key={field}
              style={{ background: '#FFF7E6', padding: '2px 4px', marginBottom: 2 }}
            >
              {field}: {String(record.feishu_values[field] ?? '-')}
            </div>
          ))}
        </div>
      ),
    },
  ];

  // ── Pull conflict columns ────────────────────────────────────────

  const pullConflictColumns: ColumnsType<ConflictRecord> = [
    {
      title: '员工',
      dataIndex: 'person_name',
      key: 'person_name',
      width: 120,
      render: (val: string | null) => val || '-',
    },
    {
      title: '冲突字段数',
      key: 'diff_count',
      width: 100,
      render: (_: unknown, record: ConflictRecord) => record.diff_fields.length,
    },
    ...(pullStrategy === 'per_record'
      ? [
          {
            title: '选择',
            key: 'choice',
            width: 160,
            render: (_: unknown, record: ConflictRecord) => (
              <Radio.Group
                value={perRecordChoices[record.record_key] || 'system'}
                onChange={(e) =>
                  setPerRecordChoices((prev) => ({
                    ...prev,
                    [record.record_key]: e.target.value,
                  }))
                }
                size="small"
              >
                <Radio value="system">系统</Radio>
                <Radio value="feishu">飞书</Radio>
              </Radio.Group>
            ),
          } as ColumnsType<ConflictRecord>[number],
        ]
      : []),
  ];

  // Pull conflict expand row
  const pullExpandedRow = (record: ConflictRecord) => {
    const diffFieldData = record.diff_fields.map((field) => ({
      field,
      system: String(record.system_values[field] ?? '-'),
      feishu: String(record.feishu_values[field] ?? '-'),
    }));

    return (
      <Table
        dataSource={diffFieldData}
        rowKey="field"
        pagination={false}
        size="small"
        columns={[
          { title: '字段名', dataIndex: 'field', key: 'field', width: 150 },
          {
            title: '系统值',
            dataIndex: 'system',
            key: 'system',
            render: (val: string, row: { field: string; system: string; feishu: string }) => (
              <span style={val !== row.feishu ? { background: '#FFF7E6', padding: '2px 4px' } : {}}>
                {val}
              </span>
            ),
          },
          {
            title: '飞书值',
            dataIndex: 'feishu',
            key: 'feishu',
            render: (val: string, row: { field: string; system: string; feishu: string }) => (
              <span style={val !== row.system ? { background: '#FFF7E6', padding: '2px 4px' } : {}}>
                {val}
              </span>
            ),
          },
        ]}
      />
    );
  };

  // ── History columns ──────────────────────────────────────────────

  const columns: ColumnsType<SyncJob> = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (val: string) => dayjs(val).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '方向',
      dataIndex: 'direction',
      key: 'direction',
      width: 80,
      render: (dir: string) => {
        const cfg = DIRECTION_CONFIG[dir] || { color: 'default', label: dir };
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
    },
    {
      title: '目标表格',
      dataIndex: 'config_id',
      key: 'config_id',
      width: 160,
      render: (id: string) => configNameMap.get(id) || id,
    },
    {
      title: '记录数',
      key: 'records',
      width: 120,
      render: (_: unknown, record: SyncJob) =>
        `${record.success_records} / ${record.total_records}`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={STATUS_COLOR[status] || 'default'}>
          {STATUS_LABEL[status] || status}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: SyncJob) =>
        record.status === 'failed' ? (
          <Button
            type="link"
            size="small"
            onClick={() => handleRetry(record.id)}
          >
            重新执行
          </Button>
        ) : null,
    },
  ];

  if (flagsLoading) return null;

  const filteredPullConflicts = pullConflicts
    ? showDiffOnly
      ? pullConflicts.conflicts.filter((c) => c.diff_fields.length > 0)
      : pullConflicts.conflicts
    : [];

  return (
    <div style={{ padding: '24px 24px 48px' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          <CloudSyncOutlined style={{ marginRight: 8 }} />
          飞书同步
        </Title>
        <Text type="secondary">
          将系统数据推送到飞书多维表格，或从飞书拉取数据
        </Text>
      </div>

      {!feishu_credentials_configured && (
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message="飞书应用凭证未配置"
          description="飞书应用凭证未配置。请在飞书设置页面配置 App ID 和 App Secret 后，即可使用同步功能。"
        />
      )}

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Select
              placeholder="选择同步目标"
              value={selectedConfigId}
              onChange={setSelectedConfigId}
              style={{ width: '100%' }}
              allowClear
              options={configs.map((c) => ({
                value: c.id,
                label: `${c.name} (${c.granularity === 'detail' ? '明细' : '汇总'})`,
              }))}
            />
          </Col>
          <Col>
            <Space>
              <Button
                type="primary"
                icon={<SyncOutlined />}
                loading={syncing}
                disabled={
                  !selectedConfigId || !feishu_credentials_configured || syncing
                }
                onClick={handlePush}
              >
                推送到飞书
              </Button>
              <Button
                loading={syncing}
                disabled={
                  !selectedConfigId || !feishu_credentials_configured || syncing
                }
                onClick={handlePull}
              >
                从飞书拉取
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {progress && (
        <Card style={{ marginBottom: 16 }}>
          <Progress
            percent={progress.percent}
            format={() => `${progress.processed} / ${progress.total}`}
            status="active"
          />
        </Card>
      )}

      <Card>
        <Table<SyncJob>
          dataSource={history}
          columns={columns}
          rowKey="id"
          loading={historyLoading}
          pagination={{ pageSize: 20 }}
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={
                  <span>
                    <Text strong>暂无同步记录</Text>
                    <br />
                    <Text type="secondary">
                      选择一个同步目标并点击推送或拉取按钮开始同步
                    </Text>
                  </span>
                }
              />
            ),
          }}
          scroll={{ x: 720 }}
        />
      </Card>

      {/* Push Conflict Modal */}
      <Modal
        title={`发现 ${pushConflicts?.total_conflicts ?? 0} 条冲突记录`}
        open={pushConflictModalOpen}
        onCancel={() => {
          setPushConflictModalOpen(false);
          setPushConflicts(null);
        }}
        width={800}
        footer={
          <Space>
            <Button
              type="primary"
              onClick={() => void handlePushConfirm('overwrite')}
            >
              覆盖飞书已有数据
            </Button>
            <Button onClick={() => void handlePushConfirm('skip')}>
              跳过已有数据
            </Button>
            <Button onClick={() => void handlePushConfirm('cancel')}>
              取消
            </Button>
          </Space>
        }
      >
        <Table<ConflictRecord>
          dataSource={pushConflicts?.conflicts ?? []}
          columns={pushConflictColumns}
          rowKey="record_key"
          pagination={false}
          scroll={{ x: 700, y: 400 }}
          size="small"
        />
      </Modal>

      {/* Pull Conflict Modal */}
      <Modal
        title={`发现 ${pullConflicts?.total_conflicts ?? 0} 条冲突记录`}
        open={pullConflictModalOpen}
        onCancel={() => {
          setPullConflictModalOpen(false);
          setPullConflicts(null);
        }}
        width={900}
        footer={
          <Space>
            <Button
              type="primary"
              onClick={() => void handlePullConfirm()}
            >
              确认拉取
            </Button>
            <Button
              onClick={() => {
                setPullConflictModalOpen(false);
                setPullConflicts(null);
              }}
            >
              取消
            </Button>
          </Space>
        }
      >
        <Row style={{ marginBottom: 16 }} align="middle" justify="space-between">
          <Col>
            <Radio.Group
              value={pullStrategy}
              onChange={(e) => setPullStrategy(e.target.value)}
            >
              <Radio.Button value="system_wins">
                以系统数据为准
              </Radio.Button>
              <Radio.Button value="feishu_wins">
                以飞书数据为准
              </Radio.Button>
              <Radio.Button value="per_record">
                逐条选择
              </Radio.Button>
            </Radio.Group>
          </Col>
          <Col>
            <Space>
              <Text type="secondary">仅显示差异</Text>
              <Switch
                checked={showDiffOnly}
                onChange={setShowDiffOnly}
              />
            </Space>
          </Col>
        </Row>

        <Table<ConflictRecord>
          dataSource={filteredPullConflicts}
          columns={pullConflictColumns}
          rowKey="record_key"
          pagination={false}
          scroll={{ x: 600, y: 400 }}
          size="small"
          expandable={{
            expandedRowRender: pullExpandedRow,
          }}
        />
      </Modal>
    </div>
  );
}

export default FeishuSyncPage;
