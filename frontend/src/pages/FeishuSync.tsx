import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Progress,
  Row,
  Select,
  Space,
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
  previewPullConflicts,
  executePull,
  readNdjsonStream,
  retrySyncJob,
  type SyncConfig,
  type SyncJob,
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
      // Silently handle — configs may not be available yet
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
        message.warning('发现冲突记录，请稍后处理');
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

  const handlePull = useCallback(async () => {
    if (!selectedConfigId) return;
    setSyncing(true);
    setProgress(null);

    try {
      const preview = await previewPullConflicts(selectedConfigId);

      if (preview.total_conflicts > 0) {
        message.warning(`发现 ${preview.total_conflicts} 条冲突记录，请稍后处理`);
        setSyncing(false);
        setProgress(null);
        return;
      }

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
    </div>
  );
}

export default FeishuSyncPage;
