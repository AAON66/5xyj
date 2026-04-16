import { useEffect, useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { App, Button, Card, Divider, Form, Input, Radio, Tabs, Typography } from 'antd';
import { ApiOutlined, LockOutlined, UserOutlined, IdcardOutlined, SolutionOutlined } from '@ant-design/icons';

import { useAuth } from '../hooks';
import { useFeishuFeatureFlag } from '../hooks/useFeishuFeatureFlag';
import { useSemanticColors } from '../theme/useSemanticColors';
import { normalizeApiError } from '../services/api';
import type { AuthRole } from '../services/authSession';
import { writeAuthSession } from '../services/authSession';
import { fetchFeishuAuthorizeUrl, feishuOAuthCallback, confirmFeishuBind } from '../services/feishu';
import type { Candidate } from '../services/feishu';
import { CandidateSelectModal } from '../components/CandidateSelectModal';

const { Title, Text } = Typography;

const DEFAULT_WORKSPACE_BY_ROLE: Record<AuthRole, string> = {
  admin: '/workspace/admin',
  hr: '/workspace/hr',
  employee: '/employee/query',
};

function resolveTargetPath(location: ReturnType<typeof useLocation>, role: AuthRole): string {
  const from = (location.state as { from?: unknown } | null)?.from;
  return typeof from === 'string' && from.startsWith('/') ? from : DEFAULT_WORKSPACE_BY_ROLE[role];
}

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, isInitializing, user, login, verifyEmployee } = useAuth();
  const { message } = App.useApp();
  const colors = useSemanticColors();

  const { feishu_oauth_enabled } = useFeishuFeatureFlag();
  const [submitting, setSubmitting] = useState(false);
  const [passwordWarning, setPasswordWarning] = useState(false);
  const [activeTab, setActiveTab] = useState<string>('credential');

  // Candidate selection state for pending_candidates flow
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [pendingToken, setPendingToken] = useState('');
  const [pendingFeishuName, setPendingFeishuName] = useState('');
  const [showCandidateModal, setShowCandidateModal] = useState(false);
  const [bindLoading, setBindLoading] = useState(false);

  // Handle Feishu OAuth callback
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');
    if (code && state && feishu_oauth_enabled) {
      // Clear URL params to prevent re-triggering on refresh
      window.history.replaceState({}, '', window.location.pathname);

      feishuOAuthCallback(code, state)
        .then((result) => {
          if (result.status === 'pending_candidates') {
            setCandidates(result.candidates);
            setPendingToken(result.pending_token);
            setPendingFeishuName(result.feishu_name);
            setShowCandidateModal(true);
          } else {
            writeAuthSession({
              accessToken: result.access_token,
              role: result.role as AuthRole,
              username: result.username,
              displayName: result.display_name,
              expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
              signedInAt: new Date().toISOString(),
            });
            window.location.href = '/';
          }
        })
        .catch(() => message.error('飞书登录失败'));
    }
  }, [feishu_oauth_enabled, message]);

  async function handleCandidateSelect(employeeMasterId: string) {
    setBindLoading(true);
    try {
      const result = await confirmFeishuBind(pendingToken, employeeMasterId);
      writeAuthSession({
        accessToken: result.access_token,
        role: result.role as AuthRole,
        username: result.username,
        displayName: result.display_name,
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        signedInAt: new Date().toISOString(),
      });
      setShowCandidateModal(false);
      window.location.href = '/';
    } catch (error) {
      message.error(normalizeApiError(error).message || '绑定失败，请重试。');
    } finally {
      setBindLoading(false);
    }
  }

  async function handleFeishuLogin() {
    try {
      const url = await fetchFeishuAuthorizeUrl();
      window.location.href = url;
    } catch {
      message.error('获取飞书授权链接失败');
    }
  }

  if (!isInitializing && isAuthenticated && user) {
    return <Navigate to={DEFAULT_WORKSPACE_BY_ROLE[user.role]} replace />;
  }

  async function handleCredentialSubmit(values: { username: string; password: string; role: string }) {
    setSubmitting(true);
    setPasswordWarning(false);

    try {
      const role = (values.role ?? 'admin') as Extract<AuthRole, 'admin' | 'hr'>;
      await login({
        username: values.username.trim(),
        password: values.password,
        role,
      });

      const session = window.localStorage.getItem('social-security-auth-session');
      if (session) {
        try {
          const parsed = JSON.parse(session);
          if (parsed.mustChangePassword) {
            setPasswordWarning(true);
            message.warning('当前密码为默认密码，请尽快修改。');
            setTimeout(() => {
              navigate(resolveTargetPath(location, role), { replace: true });
            }, 2000);
            return;
          }
        } catch {
          // ignore parse errors
        }
      }

      navigate(resolveTargetPath(location, role), { replace: true });
    } catch (error) {
      message.error(normalizeApiError(error).message || '登录失败，请检查账号、密码和角色。');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleEmployeeSubmit(values: { employee_id: string; id_number: string; name: string }) {
    setSubmitting(true);

    try {
      await verifyEmployee({
        employee_id: values.employee_id.trim(),
        id_number: values.id_number.trim(),
        person_name: values.name.trim(),
      });
      navigate('/employee/query', { replace: true });
    } catch (error) {
      const apiError = normalizeApiError(error);
      if (apiError.statusCode === 429) {
        message.error('验证失败次数过多，请15分钟后重试。');
      } else {
        message.error('身份验证失败，请检查工号、身份证号和姓名。');
      }
    } finally {
      setSubmitting(false);
    }
  }

  const tabItems = [
    {
      key: 'credential',
      label: '账号登录',
      children: (
        <Form
          layout="vertical"
          onFinish={(values) => void handleCredentialSubmit(values)}
          initialValues={{ role: 'admin' }}
          autoComplete="off"
        >
          <Form.Item name="role" label="登录角色">
            <Radio.Group buttonStyle="solid" style={{ width: '100%', display: 'flex' }}>
              <Radio.Button value="admin" style={{ flex: 1, textAlign: 'center' }}>管理员入口</Radio.Button>
              <Radio.Button value="hr" style={{ flex: 1, textAlign: 'center' }}>HR 入口</Radio.Button>
            </Radio.Group>
          </Form.Item>
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          {passwordWarning && (
            <Text type="warning" style={{ display: 'block', marginBottom: 16 }}>
              当前密码为默认密码，请尽快修改。
            </Text>
          )}
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={submitting}>
              登录
            </Button>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: 'employee',
      label: '员工查询',
      children: (
        <Form
          layout="vertical"
          onFinish={(values) => void handleEmployeeSubmit(values)}
          autoComplete="off"
        >
          <Form.Item
            name="employee_id"
            rules={[{ required: true, message: '请输入工号' }]}
          >
            <Input prefix={<IdcardOutlined />} placeholder="工号" />
          </Form.Item>
          <Form.Item
            name="id_number"
            rules={[{ required: true, message: '请输入身份证号' }]}
          >
            <Input prefix={<SolutionOutlined />} placeholder="身份证号" />
          </Form.Item>
          <Form.Item
            name="name"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="姓名" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={submitting}>
              验证身份
            </Button>
          </Form.Item>
        </Form>
      ),
    },
  ];

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: colors.BG_LAYOUT,
        paddingBottom: 40,
      }}
    >
      <Card style={{ width: 400, boxShadow: '0 1px 2px rgba(0,0,0,0.06)' }}>
        <Title level={3} style={{ textAlign: 'center', marginBottom: 24 }}>
          社保公积金管理系统
        </Title>
        <Tabs
          activeKey={activeTab}
          onChange={(key) => {
            setActiveTab(key);
            setPasswordWarning(false);
          }}
          items={tabItems}
          centered
        />
        {feishu_oauth_enabled && (
          <>
            <Divider>或</Divider>
            <Button
              block
              icon={<ApiOutlined />}
              onClick={() => void handleFeishuLogin()}
              style={{ marginBottom: 16 }}
            >
              使用飞书登录
            </Button>
          </>
        )}
        <div style={{ textAlign: 'center', marginTop: 8 }}>
          <Text type="secondary">员工自助查询仍可直接使用。</Text>{' '}
          <Link to="/employee/query">进入员工查询</Link>
        </div>
      </Card>
      <CandidateSelectModal
        open={showCandidateModal}
        candidates={candidates}
        feishuName={pendingFeishuName}
        loading={bindLoading}
        onSelect={(id) => void handleCandidateSelect(id)}
        onCancel={() => setShowCandidateModal(false)}
      />
    </div>
  );
}
