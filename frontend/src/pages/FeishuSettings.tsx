import { PlusOutlined, SettingOutlined } from '@ant-design/icons';
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Drawer,
  Form,
  Input,
  Popconfirm,
  Radio,
  Row,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useResponsiveViewport } from '../hooks/useResponsiveViewport';
import { normalizeApiError } from '../services/api';
import {
  createSyncConfig,
  deleteSyncConfig,
  fetchFeishuRuntimeSettings,
  fetchSyncConfigs,
  type FeishuRuntimeSettings,
  type FeishuRuntimeSettingsUpdate,
  type SyncConfig,
  updateFeishuCredentials,
  updateFeishuRuntimeSettings,
  updateSyncConfig,
} from '../services/feishu';
import { useFeishuFeatureFlag } from '../hooks/useFeishuFeatureFlag';

const { Title, Text } = Typography;

export function FeishuSettingsPage() {
  const navigate = useNavigate();
  const { isMobile, isTablet } = useResponsiveViewport();
  const isCompact = isMobile || isTablet;
  const {
    feishu_sync_enabled,
    feishu_oauth_enabled,
    feishu_credentials_configured,
    loading: flagsLoading,
    refreshFlags,
  } = useFeishuFeatureFlag();

  const [runtimeSettings, setRuntimeSettings] = useState<FeishuRuntimeSettings | null>(null);
  const [runtimeLoading, setRuntimeLoading] = useState(true);
  const [runtimeSubmitting, setRuntimeSubmitting] = useState(false);
  const [credentialsSubmitting, setCredentialsSubmitting] = useState(false);
  const [configs, setConfigs] = useState<SyncConfig[]>([]);
  const [configsLoading, setConfigsLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<SyncConfig | null>(null);
  const [submittingConfig, setSubmittingConfig] = useState(false);

  const [runtimeForm] = Form.useForm<FeishuRuntimeSettingsUpdate>();
  const [credentialForm] = Form.useForm<{ app_id: string; app_secret: string }>();
  const [configForm] = Form.useForm();

  const syncConfigured = runtimeSettings?.feishu_sync_enabled ?? feishu_sync_enabled;
  const oauthConfigured = runtimeSettings?.feishu_oauth_enabled ?? feishu_oauth_enabled;
  const credentialsConfigured = runtimeSettings?.feishu_credentials_configured ?? feishu_credentials_configured;

  const loadRuntimeSettings = useCallback(async () => {
    setRuntimeLoading(true);
    try {
      const data = await fetchFeishuRuntimeSettings();
      setRuntimeSettings(data);
      runtimeForm.setFieldsValue({
        feishu_sync_enabled: data.feishu_sync_enabled,
        feishu_oauth_enabled: data.feishu_oauth_enabled,
      });
    } catch (err) {
      message.error(normalizeApiError(err).message);
    } finally {
      setRuntimeLoading(false);
    }
  }, [runtimeForm]);

  const loadConfigs = useCallback(async () => {
    setConfigsLoading(true);
    try {
      const data = await fetchSyncConfigs();
      setConfigs(data);
    } catch (err) {
      message.error(normalizeApiError(err).message);
    } finally {
      setConfigsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadRuntimeSettings();
    void loadConfigs();
  }, [loadConfigs, loadRuntimeSettings]);

  const openCreateDrawer = () => {
    setEditingConfig(null);
    configForm.resetFields();
    configForm.setFieldsValue({ granularity: 'detail', field_mapping: {} });
    setDrawerOpen(true);
  };

  const openEditDrawer = (config: SyncConfig) => {
    setEditingConfig(config);
    configForm.setFieldsValue({
      name: config.name,
      app_token: config.app_token,
      table_id: config.table_id,
      granularity: config.granularity,
    });
    setDrawerOpen(true);
  };

  const handleRuntimeSubmit = async () => {
    setRuntimeSubmitting(true);
    try {
      const values = await runtimeForm.validateFields();
      const saved = await updateFeishuRuntimeSettings(values);
      setRuntimeSettings(saved);
      runtimeForm.setFieldsValue({
        feishu_sync_enabled: saved.feishu_sync_enabled,
        feishu_oauth_enabled: saved.feishu_oauth_enabled,
      });
      await refreshFlags();
      message.success('飞书运行时开关已保存');
    } catch (err) {
      message.error(normalizeApiError(err).message);
    } finally {
      setRuntimeSubmitting(false);
    }
  };

  const handleCredentialsSubmit = async () => {
    setCredentialsSubmitting(true);
    try {
      const values = await credentialForm.validateFields();
      const saved = await updateFeishuCredentials(values);
      setRuntimeSettings(saved);
      credentialForm.resetFields();
      await refreshFlags();
      message.success('飞书凭证已验证并保存');
    } catch (err) {
      message.error(normalizeApiError(err).message);
    } finally {
      setCredentialsSubmitting(false);
    }
  };

  const handleConfigSubmit = async (values: {
    name: string;
    app_token: string;
    table_id: string;
    granularity: 'detail' | 'summary';
  }) => {
    setSubmittingConfig(true);
    try {
      if (editingConfig) {
        await updateSyncConfig(editingConfig.id, values);
        message.success('同步目标已更新');
      } else {
        await createSyncConfig({ ...values, field_mapping: {} });
        message.success('同步目标已创建');
      }
      setDrawerOpen(false);
      configForm.resetFields();
      await loadConfigs();
    } catch (err) {
      message.error(normalizeApiError(err).message);
    } finally {
      setSubmittingConfig(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteSyncConfig(id);
      message.success('同步目标已删除');
      await loadConfigs();
    } catch (err) {
      message.error(normalizeApiError(err).message);
    }
  };

  const columns: ColumnsType<SyncConfig> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      fixed: 'left',
      width: 180,
    },
    {
      title: 'App Token',
      dataIndex: 'app_token',
      key: 'app_token',
      width: 160,
      render: (value: string) => <Text code>{value.slice(0, 8)}...</Text>,
    },
    {
      title: 'Table ID',
      dataIndex: 'table_id',
      key: 'table_id',
      width: 140,
      render: (value: string) => <Text code>{value}</Text>,
    },
    {
      title: '粒度',
      dataIndex: 'granularity',
      key: 'granularity',
      width: 90,
      render: (value: string) => (
        <Tag color={value === 'detail' ? 'blue' : 'orange'}>{value === 'detail' ? '明细' : '汇总'}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 90,
      render: (active: boolean) => <Tag color={active ? 'green' : 'default'}>{active ? '启用' : '停用'}</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      width: 220,
      render: (_: unknown, record: SyncConfig) => (
        <Space wrap>
          <Button type="link" size="small" onClick={() => openEditDrawer(record)}>
            编辑
          </Button>
          <Button type="link" size="small" onClick={() => navigate(`/feishu-mapping/${record.id}`)}>
            配置映射
          </Button>
          <Popconfirm
            title="确认删除此同步目标？"
            description="删除后相关同步记录仍会保留。"
            onConfirm={() => void handleDelete(record.id)}
            okText="确认"
            cancelText="取消"
          >
            <Button type="link" danger size="small">
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: isMobile ? '16px 12px 32px' : '24px 24px 48px' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          <SettingOutlined style={{ marginRight: 8 }} />
          飞书设置
        </Title>
        <Text type="secondary">在一个页面内完成飞书开关、凭证与同步目标配置。</Text>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Descriptions
          size="small"
          column={isCompact ? 1 : 3}
          items={[
            {
              key: 'sync',
              label: '同步开关',
              children: <Tag color={syncConfigured ? 'green' : 'default'}>{syncConfigured ? '已启用' : '已关闭'}</Tag>,
            },
            {
              key: 'oauth',
              label: '飞书登录',
              children: <Tag color={oauthConfigured ? 'blue' : 'default'}>{oauthConfigured ? '已启用' : '已关闭'}</Tag>,
            },
            {
              key: 'credentials',
              label: '凭证状态',
              children: (
                <Tag color={credentialsConfigured ? 'green' : 'warning'}>
                  {credentialsConfigured ? '已配置' : '未配置'}
                </Tag>
              ),
            },
          ]}
        />
      </Card>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} xl={12}>
          <Card
            title="运行时开关"
            loading={runtimeLoading && !runtimeSettings}
            extra={
              <Button
                type="primary"
                loading={runtimeSubmitting}
                onClick={() => void handleRuntimeSubmit()}
                data-testid="feishu-runtime-save"
              >
                保存开关
              </Button>
            }
          >
            <Form form={runtimeForm} layout="vertical">
              <Form.Item
                name="feishu_sync_enabled"
                label="飞书同步"
                valuePropName="checked"
                extra="关闭后同步页会进入禁用态，但设置页仍可继续维护配置。"
              >
                <Switch data-testid="feishu-sync-toggle" />
              </Form.Item>
              <Form.Item
                name="feishu_oauth_enabled"
                label="飞书登录"
                valuePropName="checked"
                extra="控制是否允许用户通过飞书 OAuth 登录。"
                style={{ marginBottom: 0 }}
              >
                <Switch data-testid="feishu-oauth-toggle" />
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col xs={24} xl={12}>
          <Card
            title="应用凭证"
            loading={runtimeLoading && !runtimeSettings}
            extra={
              <Button
                type="primary"
                loading={credentialsSubmitting}
                onClick={() => void handleCredentialsSubmit()}
                data-testid="feishu-credentials-save"
              >
                保存凭证
              </Button>
            }
          >
            {!credentialsConfigured ? (
              <Alert
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
                message="飞书应用凭证未配置"
                description="保存 App ID 和 App Secret 后，系统会验证凭证并仅展示脱敏状态。"
              />
            ) : null}

            <Descriptions
              size="small"
              column={1}
              style={{ marginBottom: 16 }}
              items={[
                {
                  key: 'configured',
                  label: '配置状态',
                  children: (
                    <Tag color={runtimeSettings?.feishu_credentials_configured ? 'green' : 'warning'}>
                      {runtimeSettings?.feishu_credentials_configured ? '已配置' : '未配置'}
                    </Tag>
                  ),
                },
                {
                  key: 'masked_app_id',
                  label: 'App ID',
                  children: runtimeSettings?.masked_app_id ? <Text code>{runtimeSettings.masked_app_id}</Text> : <Text type="secondary">尚未保存</Text>,
                },
                {
                  key: 'secret_configured',
                  label: 'Secret',
                  children: (
                    <Tag color={runtimeSettings?.secret_configured ? 'green' : 'default'}>
                      {runtimeSettings?.secret_configured ? '已保存' : '未保存'}
                    </Tag>
                  ),
                },
              ]}
            />

            <Form form={credentialForm} layout="vertical">
              <Form.Item
                name="app_id"
                label="App ID"
                rules={[{ required: true, message: '请输入飞书 App ID' }]}
              >
                <Input data-testid="feishu-app-id-input" placeholder="cli_a1b2c3..." autoComplete="off" />
              </Form.Item>
              <Form.Item
                name="app_secret"
                label="App Secret"
                rules={[{ required: true, message: '请输入飞书 App Secret' }]}
                extra="保存成功后页面只展示脱敏状态，不会回显明文 secret。"
                style={{ marginBottom: 0 }}
              >
                <Input.Password
                  data-testid="feishu-app-secret-input"
                  placeholder="输入新的 App Secret"
                  autoComplete="new-password"
                />
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>

      <Card
        title="同步目标"
        extra={
          isMobile ? null : (
            <Space wrap>
              <Button onClick={() => navigate('/feishu-sync')}>前往同步页</Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={openCreateDrawer} data-testid="feishu-sync-config-add">
                添加同步目标
              </Button>
            </Space>
          )
        }
      >
        {isMobile ? (
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
            <Button onClick={() => navigate('/feishu-sync')}>前往同步页</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreateDrawer} data-testid="feishu-sync-config-add">
              添加同步目标
            </Button>
          </div>
        ) : null}

        <Table<SyncConfig>
          dataSource={configs}
          columns={columns}
          rowKey="id"
          loading={configsLoading || flagsLoading}
          pagination={false}
          locale={{ emptyText: '暂无同步目标，请点击上方按钮添加' }}
          scroll={{ x: 820 }}
        />
      </Card>

      <Drawer
        title={editingConfig ? '编辑同步目标' : '添加同步目标'}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={isMobile ? '100vw' : 480}
        extra={
          <Space wrap>
            <Button onClick={() => setDrawerOpen(false)}>取消</Button>
            <Button
              type="primary"
              loading={submittingConfig}
              onClick={() => configForm.submit()}
              data-testid="feishu-config-submit"
            >
              {editingConfig ? '保存' : '创建'}
            </Button>
          </Space>
        }
        destroyOnClose
      >
        <Form
          form={configForm}
          layout="vertical"
          onFinish={handleConfigSubmit}
          initialValues={{ granularity: 'detail' }}
        >
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入同步目标名称' }]}
          >
            <Input placeholder="例如：社保明细同步" />
          </Form.Item>
          <Form.Item
            name="app_token"
            label="多维表格 App Token"
            rules={[{ required: true, message: '请输入 App Token' }]}
          >
            <Input placeholder="从飞书多维表格 URL 中获取" />
          </Form.Item>
          <Form.Item
            name="table_id"
            label="数据表 Table ID"
            rules={[{ required: true, message: '请输入 Table ID' }]}
          >
            <Input placeholder="从飞书多维表格的数据表设置中获取" />
          </Form.Item>
          <Form.Item
            name="granularity"
            label="数据粒度"
            rules={[{ required: true, message: '请选择数据粒度' }]}
            style={{ marginBottom: 0 }}
          >
            <Radio.Group>
              <Radio value="detail">明细</Radio>
              <Radio value="summary">汇总</Radio>
            </Radio.Group>
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  );
}

export default FeishuSettingsPage;
