import { useCallback, useEffect, useState } from 'react';
import { useSemanticColors } from '../theme/useSemanticColors';
import {
  Button,
  Card,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

import type { ApiSuccessResponse } from '../services/api';
import { apiClient, normalizeApiError } from '../services/api';
import type { ApiKeyCreateResponse, ApiKeyRead } from '../services/apiKeys';
import { createApiKey, listApiKeys, revokeApiKey } from '../services/apiKeys';

const { Title, Text, Paragraph } = Typography;

interface UserOption {
  id: string;
  username: string;
  role: string;
  display_name: string;
}

export function ApiKeysPage() {
  const colors = useSemanticColors();
  const [keys, setKeys] = useState<ApiKeyRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createdKey, setCreatedKey] = useState<ApiKeyCreateResponse | null>(null);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [form] = Form.useForm();

  const fetchKeys = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listApiKeys();
      setKeys(data.items);
    } catch (err) {
      message.error(normalizeApiError(err).message);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchUsers = useCallback(async () => {
    try {
      const resp = await apiClient.get<ApiSuccessResponse<UserOption[]>>('/users/');
      setUsers(resp.data.data);
    } catch {
      // Silently ignore -- user list may fail if not admin
    }
  }, []);

  useEffect(() => {
    fetchKeys();
    fetchUsers();
  }, [fetchKeys, fetchUsers]);

  const handleCreate = async (values: { name: string; owner_id: string }) => {
    setCreating(true);
    try {
      const result = await createApiKey(values.name, values.owner_id);
      setCreatedKey(result);
      form.resetFields();
      setCreateOpen(false);
      fetchKeys();
    } catch (err) {
      message.error(normalizeApiError(err).message);
    } finally {
      setCreating(false);
    }
  };

  const handleRevoke = async (keyId: string) => {
    try {
      await revokeApiKey(keyId);
      message.success('API Key 已禁用');
      fetchKeys();
    } catch (err) {
      message.error(normalizeApiError(err).message);
    }
  };

  const columns: ColumnsType<ApiKeyRead> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 160,
    },
    {
      title: 'Key 前缀',
      dataIndex: 'key_prefix',
      key: 'key_prefix',
      width: 120,
      render: (val: string) => <Text code>{val}...</Text>,
    },
    {
      title: '绑定用户',
      dataIndex: 'owner_username',
      key: 'owner_username',
      width: 120,
    },
    {
      title: '角色',
      dataIndex: 'owner_role',
      key: 'owner_role',
      width: 80,
      render: (role: string) => {
        const colorMap: Record<string, string> = { admin: 'red', hr: 'blue', employee: 'green' };
        return <Tag color={colorMap[role] || 'default'}>{role}</Tag>;
      },
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>{active ? '启用' : '已禁用'}</Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (val: string) => dayjs(val).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '最后使用',
      dataIndex: 'last_used_at',
      key: 'last_used_at',
      width: 140,
      render: (val: string | null) => (val ? dayjs(val).format('YYYY-MM-DD HH:mm') : '从未'),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: ApiKeyRead) =>
        record.is_active ? (
          <Popconfirm
            title="确认禁用此 API Key？"
            description="禁用后该 Key 将无法继续使用。"
            onConfirm={() => handleRevoke(record.id)}
            okText="确认"
            cancelText="取消"
          >
            <Button type="link" danger size="small">
              禁用
            </Button>
          </Popconfirm>
        ) : (
          <Text type="secondary">已禁用</Text>
        ),
    },
  ];

  return (
    <div style={{ padding: '24px 24px 48px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>
            API Key 管理
          </Title>
          <Text type="secondary">创建和管理外部程序访问系统 API 的密钥</Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          创建 API Key
        </Button>
      </div>

      <Card>
        <Table<ApiKeyRead>
          dataSource={keys}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={false}
          locale={{ emptyText: '暂无 API Key' }}
          scroll={{ x: 960 }}
        />
      </Card>

      {/* Create Modal */}
      <Modal
        title="创建 API Key"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        footer={null}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            name="name"
            label="Key 名称"
            rules={[{ required: true, message: '请输入 Key 名称' }]}
          >
            <Input placeholder="例如：外部数据同步" />
          </Form.Item>
          <Form.Item
            name="owner_id"
            label="绑定用户"
            rules={[{ required: true, message: '请选择绑定用户' }]}
          >
            <Select
              placeholder="选择要绑定的用户"
              showSearch
              optionFilterProp="label"
              options={users.map((u) => ({
                value: u.id,
                label: `${u.display_name || u.username} (${u.role})`,
              }))}
            />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={creating}>
                创建
              </Button>
              <Button onClick={() => setCreateOpen(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Created Key Display Modal */}
      <Modal
        title="API Key 已创建"
        open={!!createdKey}
        onCancel={() => setCreatedKey(null)}
        onOk={() => setCreatedKey(null)}
        okText="我已复制"
        cancelButtonProps={{ style: { display: 'none' } }}
      >
        {createdKey && (
          <div>
            <Paragraph type="warning" strong>
              API Key 仅显示一次，请立即复制保存
            </Paragraph>
            <div style={{ marginBottom: 12 }}>
              <Text type="secondary">Key 名称：</Text>
              <Text strong>{createdKey.name}</Text>
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text type="secondary">绑定用户：</Text>
              <Text>{createdKey.owner_username} ({createdKey.owner_role})</Text>
            </div>
            <div style={{ background: colors.FILL_QUATERNARY, padding: '12px 16px', borderRadius: 6 }}>
              <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>API Key：</Text>
              <Text copyable strong style={{ fontSize: 14, wordBreak: 'break-all' }}>
                {createdKey.key}
              </Text>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

export default ApiKeysPage;
