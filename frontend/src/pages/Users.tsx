import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Button,
  Form,
  Input,
  message,
  Modal,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
} from 'antd';
import { UserAddOutlined, EditOutlined, LockOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import axios from 'axios';
import dayjs from 'dayjs';

import { useAuth } from '../hooks/useAuth';
import {
  createUser,
  fetchUsers,
  resetUserPassword,
  updateUser,
  type CreateUserInput,
  type UpdateUserInput,
  type UserItem,
} from '../services/users';

const { Title } = Typography;

const ROLE_OPTIONS = [
  { label: '管理员', value: 'admin' as const },
  { label: 'HR', value: 'hr' as const },
];

export function UsersPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  // Create modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [createForm] = Form.useForm<CreateUserInput & { confirm_password: string }>();

  // Edit modal
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [editingUser, setEditingUser] = useState<UserItem | null>(null);
  const [editForm] = Form.useForm<UpdateUserInput>();

  // Reset password modal
  const [resetPasswordModalOpen, setResetPasswordModalOpen] = useState(false);
  const [resetPasswordLoading, setResetPasswordLoading] = useState(false);
  const [resetPasswordUserId, setResetPasswordUserId] = useState<string | null>(null);
  const [resetPasswordForm] = Form.useForm<{ new_password: string }>();

  // Find current user's ID from the user list
  const currentUserId = useMemo(() => {
    if (!user) return null;
    const match = users.find((u) => u.username === user.username);
    return match?.id ?? null;
  }, [users, user]);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchUsers();
      setUsers(data);
    } catch {
      message.error('加载用户列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  // Toggle user active status
  const handleToggleActive = async (record: UserItem, checked: boolean) => {
    setTogglingId(record.id);
    try {
      await updateUser(record.id, { is_active: checked });
      message.success('用户信息已更新');
      await loadUsers();
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 403) {
        message.error(err.response?.data?.detail || '操作被拒绝');
      } else {
        message.error('更新失败');
      }
    } finally {
      setTogglingId(null);
    }
  };

  // Create user
  const handleCreateSubmit = async () => {
    try {
      const values = await createForm.validateFields();
      setCreateLoading(true);
      const { confirm_password: _, ...input } = values;
      await createUser(input);
      message.success('用户创建成功');
      setCreateModalOpen(false);
      createForm.resetFields();
      await loadUsers();
    } catch (err) {
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 409) {
          createForm.setFields([{ name: 'username', errors: ['该用户名已存在'] }]);
        } else if (err.response?.data?.detail) {
          message.error(err.response.data.detail);
        } else {
          message.error('创建失败');
        }
      }
      // validation errors from form.validateFields are silently ignored
    } finally {
      setCreateLoading(false);
    }
  };

  // Edit user
  const handleEditOpen = (record: UserItem) => {
    setEditingUser(record);
    editForm.setFieldsValue({
      display_name: record.display_name,
      role: record.role,
    });
    setEditModalOpen(true);
  };

  const handleEditSubmit = async () => {
    if (!editingUser) return;
    try {
      const values = await editForm.validateFields();
      setEditLoading(true);
      await updateUser(editingUser.id, values);
      message.success('用户信息已更新');
      setEditModalOpen(false);
      setEditingUser(null);
      editForm.resetFields();
      await loadUsers();
    } catch (err) {
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 403) {
          message.error(err.response?.data?.detail || '操作被拒绝');
        } else if (err.response?.data?.detail) {
          message.error(err.response.data.detail);
        } else {
          message.error('更新失败');
        }
      }
    } finally {
      setEditLoading(false);
    }
  };

  // Reset password
  const handleResetPasswordConfirm = (userId: string) => {
    setResetPasswordUserId(userId);
    setResetPasswordModalOpen(true);
  };

  const handleResetPasswordSubmit = async () => {
    if (!resetPasswordUserId) return;
    try {
      const values = await resetPasswordForm.validateFields();
      setResetPasswordLoading(true);
      await resetUserPassword(resetPasswordUserId, values.new_password);
      message.success('密码已重置，用户下次登录需修改密码');
      setResetPasswordModalOpen(false);
      setResetPasswordUserId(null);
      resetPasswordForm.resetFields();
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        message.error(err.response.data.detail);
      } else {
        message.error('重置密码失败');
      }
    } finally {
      setResetPasswordLoading(false);
    }
  };

  const columns: ColumnsType<UserItem> = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      width: 140,
    },
    {
      title: '显示名',
      dataIndex: 'display_name',
      key: 'display_name',
      width: 140,
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      width: 100,
      render: (role: string) => (
        <Tag color={role === 'admin' ? 'blue' : 'green'}>
          {role === 'admin' ? '管理员' : 'HR'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive: boolean, record: UserItem) => (
        <Switch
          checked={isActive}
          disabled={record.id === currentUserId}
          loading={togglingId === record.id}
          onChange={(checked) => handleToggleActive(record, checked)}
        />
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
      title: '操作',
      key: 'actions',
      width: 140,
      render: (_: unknown, record: UserItem) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEditOpen(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确认重置该用户的密码？"
            description="重置后用户将被要求首次登录时修改密码。"
            okText="确认重置"
            okType="danger"
            cancelText="取消"
            onConfirm={() => handleResetPasswordConfirm(record.id)}
          >
            <Button type="link" size="small" danger>
              重置密码
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>账号管理</Title>
        <Button type="primary" icon={<UserAddOutlined />} onClick={() => setCreateModalOpen(true)}>
          创建用户
        </Button>
      </div>

      <Table<UserItem>
        size="small"
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={users}
        pagination={{ pageSize: 20, hideOnSinglePage: true }}
        locale={{ emptyText: '暂无用户' }}
      />

      {/* Create user modal */}
      <Modal
        title="创建用户"
        open={createModalOpen}
        width={480}
        okText="确定"
        cancelText="取消"
        confirmLoading={createLoading}
        onOk={handleCreateSubmit}
        onCancel={() => { setCreateModalOpen(false); createForm.resetFields(); }}
        destroyOnClose
      >
        <Form form={createForm} layout="vertical" autoComplete="off">
          <Form.Item
            name="username"
            label="用户名"
            rules={[
              { required: true, message: '请输入用户名' },
              { max: 50, message: '用户名不能超过50个字符' },
            ]}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>
          <Form.Item
            name="display_name"
            label="显示名"
            rules={[
              { required: true, message: '请输入显示名' },
              { max: 50, message: '显示名不能超过50个字符' },
            ]}
          >
            <Input placeholder="请输入显示名" />
          </Form.Item>
          <Form.Item
            name="role"
            label="角色"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select placeholder="请选择角色" options={ROLE_OPTIONS} />
          </Form.Item>
          <Form.Item
            name="password"
            label="初始密码"
            rules={[
              { required: true, message: '请输入初始密码' },
              { min: 8, message: '密码至少8位' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="请输入初始密码" />
          </Form.Item>
          <Form.Item
            name="confirm_password"
            label="确认密码"
            dependencies={['password']}
            rules={[
              { required: true, message: '请再次输入密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="请再次输入密码" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit user modal */}
      <Modal
        title="编辑用户"
        open={editModalOpen}
        width={480}
        okText="确定"
        cancelText="取消"
        confirmLoading={editLoading}
        onOk={handleEditSubmit}
        onCancel={() => { setEditModalOpen(false); setEditingUser(null); editForm.resetFields(); }}
        destroyOnClose
      >
        <Form form={editForm} layout="vertical" autoComplete="off">
          <Form.Item label="用户名">
            <Input value={editingUser?.username} disabled />
          </Form.Item>
          <Form.Item
            name="display_name"
            label="显示名"
            rules={[{ required: true, message: '请输入显示名' }]}
          >
            <Input placeholder="请输入显示名" />
          </Form.Item>
          <Form.Item
            name="role"
            label="角色"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select
              placeholder="请选择角色"
              options={ROLE_OPTIONS}
              disabled={editingUser?.id === currentUserId}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Reset password modal */}
      <Modal
        title="设置新密码"
        open={resetPasswordModalOpen}
        width={400}
        okText="确定"
        cancelText="取消"
        confirmLoading={resetPasswordLoading}
        onOk={handleResetPasswordSubmit}
        onCancel={() => { setResetPasswordModalOpen(false); setResetPasswordUserId(null); resetPasswordForm.resetFields(); }}
        destroyOnClose
      >
        <Form form={resetPasswordForm} layout="vertical" autoComplete="off">
          <Form.Item
            name="new_password"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 8, message: '密码至少8位' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="请输入新密码（至少8位）" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default UsersPage;
