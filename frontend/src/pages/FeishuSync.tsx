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
  success: '\u6210\u529F',
  failed: '\u5931\u8D25',
  partial: '\u90E8\u5206\u6210\u529F',
  running: '\u8FD0\u884C\u4E2D',
  pending: '\u7B49\u5F85\u4E2D',
};

const DIRECTION_CONFIG: Record<string, { color: string; label: string }> = {
  push: { color: 'blue', label: '\u63A8\u9001' },
  pull: { color: 'green', label: '\u62C9\u53D6' },
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
        message.error(`\u63A8\u9001\u5931\u8D25: ${errorText}`);
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
        message.success('\u63A8\u9001\u5B8C\u6210');
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
            message.success('\u540C\u6B65\u5B8C\u6210');
          }
          if (event.type === 'error') {
            message.error(String(event.message ?? '\u540C\u6B65\u51FA\u9519'));
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
          message.error(`\u64CD\u4F5C\u5931\u8D25: ${errorText}`);
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
            message.success('\u63A8\u9001\u5B8C\u6210');
          }
          if (event.type === 'error') {
            message.error(String(event.message ?? '\u63A8\u9001\u51FA\u9519'));
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
        message.error(`\u62C9\u53D6\u5931\u8D25: ${errorText}`);
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
          message.success('\u62C9\u53D6\u5B8C\u6210');
        }
        if (event.type === 'error') {
          message.error(String(event.message ?? '\u62C9\u53D6\u51FA\u9519'));
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
        message.error(`\u62C9\u53D6\u5931\u8D25: ${errorText}`);
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
          message.success('\u62C9\u53D6\u5B8C\u6210');
        }
        if (event.type === 'error') {
          message.error(String(event.message ?? '\u62C9\u53D6\u51FA\u9519'));
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
        message.success('\u5DF2\u91CD\u65B0\u89E6\u53D1\u540C\u6B65');
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
      title: '\u5458\u5DE5',
      dataIndex: 'person_name',
      key: 'person_name',
      width: 100,
      render: (val: string | null) => val || '-',
    },
    {
      title: '\u5B57\u6BB5',
      dataIndex: 'diff_fields',
      key: 'diff_fields',
      width: 200,
      render: (fields: string[]) => fields.join(', '),
    },
    {
      title: '\u7CFB\u7EDF\u503C',
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
      title: '\u98DE\u4E66\u503C',
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
      title: '\u5458\u5DE5',
      dataIndex: 'person_name',
      key: 'person_name',
      width: 120,
      render: (val: string | null) => val || '-',
    },
    {
      title: '\u51B2\u7A81\u5B57\u6BB5\u6570',
      key: 'diff_count',
      width: 100,
      render: (_: unknown, record: ConflictRecord) => record.diff_fields.length,
    },
    ...(pullStrategy === 'per_record'
      ? [
          {
            title: '\u9009\u62E9',
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
                <Radio value="system">\u7CFB\u7EDF</Radio>
                <Radio value="feishu">\u98DE\u4E66</Radio>
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
          { title: '\u5B57\u6BB5\u540D', dataIndex: 'field', key: 'field', width: 150 },
          {
            title: '\u7CFB\u7EDF\u503C',
            dataIndex: 'system',
            key: 'system',
            render: (val: string, row: { field: string; system: string; feishu: string }) => (
              <span style={val !== row.feishu ? { background: '#FFF7E6', padding: '2px 4px' } : {}}>
                {val}
              </span>
            ),
          },
          {
            title: '\u98DE\u4E66\u503C',
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
      title: '\u65F6\u95F4',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (val: string) => dayjs(val).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '\u65B9\u5411',
      dataIndex: 'direction',
      key: 'direction',
      width: 80,
      render: (dir: string) => {
        const cfg = DIRECTION_CONFIG[dir] || { color: 'default', label: dir };
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
    },
    {
      title: '\u76EE\u6807\u8868\u683C',
      dataIndex: 'config_id',
      key: 'config_id',
      width: 160,
      render: (id: string) => configNameMap.get(id) || id,
    },
    {
      title: '\u8BB0\u5F55\u6570',
      key: 'records',
      width: 120,
      render: (_: unknown, record: SyncJob) =>
        `${record.success_records} / ${record.total_records}`,
    },
    {
      title: '\u72B6\u6001',
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
      title: '\u64CD\u4F5C',
      key: 'action',
      width: 100,
      render: (_: unknown, record: SyncJob) =>
        record.status === 'failed' ? (
          <Button
            type="link"
            size="small"
            onClick={() => handleRetry(record.id)}
          >
            \u91CD\u65B0\u6267\u884C
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
          \u98DE\u4E66\u540C\u6B65
        </Title>
        <Text type="secondary">
          \u5C06\u7CFB\u7EDF\u6570\u636E\u63A8\u9001\u5230\u98DE\u4E66\u591A\u7EF4\u8868\u683C\uFF0C\u6216\u4ECE\u98DE\u4E66\u62C9\u53D6\u6570\u636E
        </Text>
      </div>

      {!feishu_credentials_configured && (
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message="\u98DE\u4E66\u5E94\u7528\u51ED\u8BC1\u672A\u914D\u7F6E"
          description="\u98DE\u4E66\u5E94\u7528\u51ED\u8BC1\u672A\u914D\u7F6E\u3002\u8BF7\u5728\u98DE\u4E66\u8BBE\u7F6E\u9875\u9762\u914D\u7F6E App ID \u548C App Secret \u540E\uFF0C\u5373\u53EF\u4F7F\u7528\u540C\u6B65\u529F\u80FD\u3002"
        />
      )}

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Select
              placeholder="\u9009\u62E9\u540C\u6B65\u76EE\u6807"
              value={selectedConfigId}
              onChange={setSelectedConfigId}
              style={{ width: '100%' }}
              allowClear
              options={configs.map((c) => ({
                value: c.id,
                label: `${c.name} (${c.granularity === 'detail' ? '\u660E\u7EC6' : '\u6C47\u603B'})`,
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
                \u63A8\u9001\u5230\u98DE\u4E66
              </Button>
              <Button
                loading={syncing}
                disabled={
                  !selectedConfigId || !feishu_credentials_configured || syncing
                }
                onClick={handlePull}
              >
                \u4ECE\u98DE\u4E66\u62C9\u53D6
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
                    <Text strong>\u6682\u65E0\u540C\u6B65\u8BB0\u5F55</Text>
                    <br />
                    <Text type="secondary">
                      \u9009\u62E9\u4E00\u4E2A\u540C\u6B65\u76EE\u6807\u5E76\u70B9\u51FB\u63A8\u9001\u6216\u62C9\u53D6\u6309\u94AE\u5F00\u59CB\u540C\u6B65
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
        title={`\u53D1\u73B0 ${pushConflicts?.total_conflicts ?? 0} \u6761\u51B2\u7A81\u8BB0\u5F55`}
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
              \u8986\u76D6\u98DE\u4E66\u5DF2\u6709\u6570\u636E
            </Button>
            <Button onClick={() => void handlePushConfirm('skip')}>
              \u8DF3\u8FC7\u5DF2\u6709\u6570\u636E
            </Button>
            <Button onClick={() => void handlePushConfirm('cancel')}>
              \u53D6\u6D88
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
        title={`\u53D1\u73B0 ${pullConflicts?.total_conflicts ?? 0} \u6761\u51B2\u7A81\u8BB0\u5F55`}
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
              \u786E\u8BA4\u62C9\u53D6
            </Button>
            <Button
              onClick={() => {
                setPullConflictModalOpen(false);
                setPullConflicts(null);
              }}
            >
              \u53D6\u6D88
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
                \u4EE5\u7CFB\u7EDF\u6570\u636E\u4E3A\u51C6
              </Radio.Button>
              <Radio.Button value="feishu_wins">
                \u4EE5\u98DE\u4E66\u6570\u636E\u4E3A\u51C6
              </Radio.Button>
              <Radio.Button value="per_record">
                \u9010\u6761\u9009\u62E9
              </Radio.Button>
            </Radio.Group>
          </Col>
          <Col>
            <Space>
              <Text type="secondary">\u4EC5\u663E\u793A\u5DEE\u5F02</Text>
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
