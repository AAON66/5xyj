import { useState } from 'react';
import { Modal, Form, Input, message, Alert } from 'antd';
import { LockOutlined } from '@ant-design/icons';
import axios from 'axios';

import { changeOwnPassword } from '../services/auth';
import { readAuthSession, writeAuthSession } from '../services/authSession';

interface ChangePasswordModalProps {
  open: boolean;
  forced?: boolean;
  onSuccess: () => void;
  onCancel?: () => void;
}

interface ChangePasswordFormValues {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export function ChangePasswordModal({ open, forced = false, onSuccess, onCancel }: ChangePasswordModalProps) {
  const [form] = Form.useForm<ChangePasswordFormValues>();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      await changeOwnPassword(values.old_password, values.new_password);

      // Update session to clear mustChangePassword flag
      // writeAuthSession dispatches AUTH_SESSION_EVENT automatically
      // AuthProvider listens to this event and calls setSession(readAuthSession())
      // This ensures user.mustChangePassword syncs in memory
      const session = readAuthSession();
      if (session) {
        writeAuthSession({ ...session, mustChangePassword: false });
      }

      message.success('密码修改成功');
      form.resetFields();
      onSuccess();
    } catch (err) {
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 400) {
          form.setFields([{ name: 'old_password', errors: ['当前密码错误，请重新输入'] }]);
        } else if (err.response?.status === 403) {
          message.error('当前账号类型不支持修改密码');
        } else {
          message.error(err.response?.data?.detail || '密码修改失败');
        }
      }
      // validation errors from form.validateFields are silently ignored
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel?.();
  };

  return (
    <Modal
      title="修改密码"
      open={open}
      width={420}
      okText="确定"
      cancelText="取消"
      confirmLoading={loading}
      onOk={handleSubmit}
      onCancel={forced ? undefined : handleCancel}
      closable={!forced}
      maskClosable={!forced}
      keyboard={!forced}
      footer={forced ? undefined : undefined}
      cancelButtonProps={forced ? { style: { display: 'none' } } : undefined}
      destroyOnClose
    >
      {forced && (
        <Alert
          type="info"
          message="您的密码需要修改，请设置新密码后继续使用系统"
          style={{ marginBottom: 16 }}
        />
      )}
      <Form form={form} layout="vertical" autoComplete="off">
        <Form.Item
          name="old_password"
          label="当前密码"
          rules={[{ required: true, message: '请输入当前密码' }]}
        >
          <Input.Password prefix={<LockOutlined />} placeholder="请输入当前密码" />
        </Form.Item>
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
        <Form.Item
          name="confirm_password"
          label="确认新密码"
          dependencies={['new_password']}
          rules={[
            { required: true, message: '请再次输入新密码' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('new_password') === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('两次输入的密码不一致'));
              },
            }),
          ]}
        >
          <Input.Password prefix={<LockOutlined />} placeholder="请再次输入新密码" />
        </Form.Item>
      </Form>
    </Modal>
  );
}

export default ChangePasswordModal;
