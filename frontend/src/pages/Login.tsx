import { lazy, Suspense, useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { App, Button, Card, Divider, Form, Input, Radio, Tabs, Typography } from 'antd';
import { ApiOutlined, LockOutlined, UserOutlined, IdcardOutlined, SolutionOutlined } from '@ant-design/icons';

import { useAuth } from '../hooks';
import { useFeishuFeatureFlag } from '../hooks/useFeishuFeatureFlag';
import { useResponsiveViewport } from '../hooks/useResponsiveViewport';
import { useSemanticColors } from '../theme/useSemanticColors';
import { useThemeMode } from '../theme/useThemeMode';
import { useWebGLSupport } from '../hooks/useWebGLSupport';
import { normalizeApiError } from '../services/api';
import type { AuthRole } from '../services/authSession';
import { writeAuthSession } from '../services/authSession';
import { fetchFeishuAuthorizeUrl, feishuOAuthCallback, confirmFeishuBind } from '../services/feishu';
import type { Candidate } from '../services/feishu';
import { CandidateSelectModal } from '../components/CandidateSelectModal';
import { CssGradientBackground } from '../components/CssGradientBackground';
import { BrandPanel } from '../components/BrandPanel';

// Lazy-loaded ParticleWave (Plan 02): Three.js + shaders live in a separate chunk
// so the login first-paint is not blocked by ~155KB gzip of `three`. Declared at
// module top-level so the lazy component identity is stable across renders.
const ParticleWave = lazy(() => import('../components/ParticleWave'));

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

  // Phase 23 visual hooks
  const { isMobile } = useResponsiveViewport();
  const { isDark } = useThemeMode();
  const webgl = useWebGLSupport();

  // UI-SPEC Layout Contract locks the desktop breakpoint at 1024px (Ant Design's
  // `lg` boundary is 992px, which is 32px too narrow). We drive the split with an
  // independent matchMedia('(min-width: 1024px)') listener to preserve the
  // contract; useResponsiveViewport still owns the 767px mobile split below.
  const [isDesktop1024, setIsDesktop1024] = useState<boolean>(() => {
    if (typeof window === 'undefined') return true;
    return window.matchMedia('(min-width: 1024px)').matches;
  });
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const mq = window.matchMedia('(min-width: 1024px)');
    const sync = () => setIsDesktop1024(mq.matches);
    sync();
    if ('addEventListener' in mq) {
      mq.addEventListener('change', sync);
      return () => mq.removeEventListener('change', sync);
    }
    // Legacy Safari fallback
    const legacy = mq as MediaQueryList & {
      addListener?: (l: () => void) => void;
      removeListener?: (l: () => void) => void;
    };
    legacy.addListener?.(sync);
    return () => legacy.removeListener?.(sync);
  }, []);

  // Handle Feishu OAuth callback
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');
    if (code && state) {
      // Bind callback: state starts with "bind:" → forward to settings page
      if (state.startsWith('bind:')) {
        window.location.href = `/settings?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}&action=bind`;
        return;
      }

      if (!feishu_oauth_enabled) return;

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

  // Document title — UI-SPEC Copywriting Contract
  useEffect(() => {
    const prev = document.title;
    document.title = '登录 · 社保公积金管理系统';
    return () => {
      document.title = prev;
    };
  }, []);

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

  // === Left-panel canvas — routes WebGL vs CSS fallback ===
  // - webgl === 'fallback': render CssGradientBackground directly (no lazy chunk)
  // - webgl === 'webgl' | 'loading': render lazy ParticleWave; Suspense fallback
  //   is the same CssGradientBackground so the 0-50ms chunk-load window never
  //   flashes a plain white panel.
  const LeftCanvas = () => {
    if (webgl === 'fallback') return <CssGradientBackground isDark={isDark} />;
    return (
      <Suspense fallback={<CssGradientBackground isDark={isDark} />}>
        <ParticleWave isDark={isDark} />
      </Suspense>
    );
  };

  // === Form card style — isDark toggles glass morphism ===
  // Light: solid white with subtle shadow (preserved from previous Login.tsx).
  // Dark: translucent surface + backdrop-filter blur(20px) saturate(180%) per
  // UI-SPEC Color. Both -webkit- and standard prefixes are set: Safari 18 still
  // requires -webkit-backdrop-filter. No box-shadow on the dark variant (UI-SPEC
  // explicitly avoids box-shadow + backdrop-filter combo due to Safari bug).
  const cardStyle: CSSProperties = isDark
    ? {
        width: 400,
        background: 'rgba(30, 35, 45, 0.72)',
        WebkitBackdropFilter: 'blur(20px) saturate(180%)',
        backdropFilter: 'blur(20px) saturate(180%)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: 12,
        boxShadow: 'none',
      }
    : {
        width: 400,
        background: '#FFFFFF',
        borderRadius: 12,
        boxShadow: '0 1px 2px rgba(0,0,0,0.06)',
      };

  // === Breakpoint-driven flex sizes (UI-SPEC Layout Contract) ===
  // - Mobile (≤767, isMobile):   right flex 1 1 100%, left not rendered
  // - Tablet (768-1023, !isDesktop1024): left 50%, right 50%
  // - Desktop (≥1024, isDesktop1024):    left 60%, right 40%
  const leftFlex = isDesktop1024 ? '0 0 60%' : '0 0 50%';
  const rightFlex = isMobile ? '1 1 100%' : isDesktop1024 ? '0 0 40%' : '0 0 50%';

  return (
    <div
      style={{
        display: 'flex',
        minHeight: '100vh',
        background: isDark ? '#141414' : colors.BG_LAYOUT,
      }}
    >
      {!isMobile && (
        <div
          style={{
            flex: leftFlex,
            position: 'relative',
            overflow: 'hidden',
            minHeight: '100vh',
          }}
        >
          <LeftCanvas />
          <BrandPanel isDark={isDark} />
        </div>
      )}
      <div
        style={{
          flex: rightFlex,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 32,
          minHeight: '100vh',
        }}
      >
        <Card style={cardStyle} data-testid="login-form-card">
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
      </div>
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
