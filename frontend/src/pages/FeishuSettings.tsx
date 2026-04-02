import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Drawer,
  Form,
  Input,
  Popconfirm,
  Radio,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { PlusOutlined, SettingOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

import { normalizeApiError } from '../services/api';
import {
  fetchSyncConfigs,
  createSyncConfig,
  updateSyncConfig,
  deleteSyncConfig,
  type SyncConfig,
} from '../services/feishu';
import { useFeishuFeatureFlag } from '../hooks/useFeishuFeatureFlag';

const { Title, Text } = Typography;

export function FeishuSettingsPage() {
  const navigate = useNavigate();
  const {
    feishu_sync_enabled,
    feishu_oauth_enabled,
    feishu_credentials_configured,
    loading: flagsLoading,
  } = useFeishuFeatureFlag();

  const [configs, setConfigs] = useState<SyncConfig[]>([]);
  const [configsLoading, setConfigsLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<SyncConfig | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();

  // Redirect when feature is disabled
  useEffect(() => {
    if (!flagsLoading && !feishu_sync_enabled) {
      navigate('/');
    }
  }, [flagsLoading, feishu_sync_enabled, navigate]);

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
    loadConfigs();
  }, [loadConfigs]);

  const openCreateDrawer = () => {
    setEditingConfig(null);
    form.resetFields();
    form.setFieldsValue({ granularity: 'detail', field_mapping: {} });
    setDrawerOpen(true);
  };

  const openEditDrawer = (config: SyncConfig) => {
    setEditingConfig(config);
    form.setFieldsValue({
      name: config.name,
      app_token: config.app_token,
      table_id: config.table_id,
      granularity: config.granularity,
    });
    setDrawerOpen(true);
  };

  const handleSubmit = async (values: {
    name: string;
    app_token: string;
    table_id: string;
    granularity: 'detail' | 'summary';
  }) => {
    setSubmitting(true);
    try {
      if (editingConfig) {
        await updateSyncConfig(editingConfig.id, values);
        message.success('同步目标已更新');
      } else {
        await createSyncConfig({ ...values, field_mapping: {} });
        message.success('同步目标已创建');
      }
      setDrawerOpen(false);
      form.resetFields();
      loadConfigs();
    } catch (err) {
      message.error(normalizeApiError(err).message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteSyncConfig(id);
      message.success('同步目标已删除');
      loadConfigs();
    } catch (err) {
      message.error(normalizeApiError(err).message);
    }
  };

  const columns: ColumnsType<SyncConfig> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 180,
    },
    {
      title: 'App Token',
      dataIndex: 'app_token',
      key: 'app_token',
      width: 160,
      render: (val: string) => (
        <Text code>{val.slice(0, 8)}{'...'}</Text>
      ),
    },
    {
      title: '粒度',
      dataIndex: 'granularity',
      key: 'granularity',
      width: 80,
      render: (val: string) => (
        <Tag color={val === 'detail' ? 'blue' : 'orange'}>
          {val === 'detail' ? '明细' : '汇总'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'default'}>
          {active ? '启用' : '停用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: unknown, record: SyncConfig) => (
        <Space>
          <Button
            type="link"
            size="small"
            onClick={() => openEditDrawer(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => navigate(`/feishu-mapping/${record.id}`)}
          >
            配置映射
          </Button>
          <Popconfirm
            title="确认删除此同步目标？"
            description="删除后相关同步记录仍会保留。"
            onConfirm={() => handleDelete(record.id)}
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

  if (flagsLoading) return null;

  return (
    <div style={{ padding: '24px 24px 48px' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          <SettingOutlined style={{ marginRight: 8 }} />
          飞书设置
        </Title>
        <Text type="secondary">管理飞书集成的功能开关、应用凭证和同步目标</Text>
      </div>

      {/* Feature Toggles */}
      <Card title="功能开关" style={{ marginBottom: 16 }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 12,
          }}
        >
          <div>
            <Text strong>飞书同步</Text>
            <br />
            <Text type="secondary">
              启用后可将系统数据同步到飞书多维表格
            </Text>
          </div>
          <Switch checked={feishu_sync_enabled} disabled />
        </div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <Text strong>飞书登录</Text>
            <br />
            <Text type="secondary">允许用户使用飞书账号登录系统</Text>
          </div>
          <Switch checked={feishu_oauth_enabled} disabled />
        </div>
      </Card>

      {/* Credentials */}
      <Card title="应用凭证" style={{ marginBottom: 16 }}>
        {!feishu_credentials_configured ? (
          <Alert
            type="info"
            showIcon
            message="飞书应用凭证未配置"
            description="请在服务器环境变量中配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET，然后重启服务。"
          />
        ) : (
          <Descriptions column={1} size="small">
            <Descriptions.Item label="凭证状态">
              <Tag color="green">已配置</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="App ID">
              <Text code>{'****'}</Text>
              <Text type="secondary" style={{ marginLeft: 8 }}>
                (已脱敏)
              </Text>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Card>

      {/* Sync Targets */}
      <Card
        title="同步目标"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={openCreateDrawer}
          >
            添加同步目标
          </Button>
        }
      >
        <Table<SyncConfig>
          dataSource={configs}
          columns={columns}
          rowKey="id"
          loading={configsLoading}
          pagination={false}
          locale={{ emptyText: '暂无同步目标，请点击上方按钮添加' }}
          scroll={{ x: 700 }}
        />
      </Card>

      {/* Add/Edit Drawer */}
      <Drawer
        title={editingConfig ? '编辑同步目标' : '添加同步目标'}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={480}
        extra={
          <Space>
            <Button onClick={() => setDrawerOpen(false)}>取消</Button>
            <Button type="primary" loading={submitting} onClick={() => form.submit()}>
              {editingConfig ? '保存' : '创建'}
            </Button>
          </Space>
        }
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
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
