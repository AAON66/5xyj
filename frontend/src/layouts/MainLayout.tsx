import { useState, useEffect, useRef, type PropsWithChildren } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Layout,
  Menu,
  Breadcrumb,
  Button,
  Dropdown,
  Alert,
  Space,
} from 'antd';
import type { MenuProps } from 'antd';
import {
  UploadOutlined,
  DashboardOutlined,
  SwapOutlined,
  ImportOutlined,
  ToolOutlined,
  CheckCircleOutlined,
  ExportOutlined,
  TeamOutlined,
  DatabaseOutlined,
  AuditOutlined,
  LogoutOutlined,
  SearchOutlined,
  UserOutlined,
} from '@ant-design/icons';

import { useAuth } from '../hooks/useAuth';
import { useAggregateSession } from '../hooks/useAggregateSession';
import { useApiFeedback } from '../hooks/useApiFeedback';
import { cancelAggregateSession, clearAggregateSession } from '../services/aggregateSessionStore';
import animations from '../theme/animations.module.css';
import styles from './MainLayout.module.css';

const { Header, Sider, Content } = Layout;

interface NavItem {
  key: string;
  icon: React.ReactNode;
  label: string;
  roles: string[];
}

const ALL_NAV_ITEMS: NavItem[] = [
  { key: '/aggregate', icon: <UploadOutlined />, label: '\u5FEB\u901F\u878D\u5408', roles: ['admin', 'hr'] },
  { key: '/dashboard', icon: <DashboardOutlined />, label: '\u5904\u7406\u770B\u677F', roles: ['admin', 'hr'] },
  { key: '/compare', icon: <SwapOutlined />, label: '\u6708\u5EA6\u5BF9\u6BD4', roles: ['admin', 'hr'] },
  { key: '/imports', icon: <ImportOutlined />, label: '\u6279\u6B21\u7BA1\u7406', roles: ['admin', 'hr'] },
  { key: '/mappings', icon: <ToolOutlined />, label: '\u6620\u5C04\u4FEE\u6B63', roles: ['admin', 'hr'] },
  { key: '/results', icon: <CheckCircleOutlined />, label: '\u6821\u9A8C\u5339\u914D', roles: ['admin', 'hr'] },
  { key: '/exports', icon: <ExportOutlined />, label: '\u5BFC\u51FA\u7ED3\u679C', roles: ['admin', 'hr'] },
  { key: '/employees', icon: <TeamOutlined />, label: '\u5458\u5DE5\u4E3B\u6863', roles: ['admin', 'hr'] },
  { key: '/data-management', icon: <DatabaseOutlined />, label: '\u6570\u636E\u7BA1\u7406', roles: ['admin', 'hr'] },
  { key: '/audit-logs', icon: <AuditOutlined />, label: '\u5BA1\u8BA1\u65E5\u5FD7', roles: ['admin'] },
  { key: '/employee/query', icon: <SearchOutlined />, label: '\u5458\u5DE5\u67E5\u8BE2', roles: ['employee'] },
];

function buildMenuItems(userRole: string): MenuProps['items'] {
  return ALL_NAV_ITEMS
    .filter((item) => item.roles.includes(userRole))
    .map((item) => ({
      key: item.key,
      icon: item.icon,
      label: item.label,
    }));
}

const LABEL_MAP: Record<string, string> = {
  aggregate: '\u5FEB\u901F\u878D\u5408',
  dashboard: '\u5904\u7406\u770B\u677F',
  compare: '\u6708\u5EA6\u5BF9\u6BD4',
  imports: '\u6279\u6B21\u7BA1\u7406',
  mappings: '\u6620\u5C04\u4FEE\u6B63',
  results: '\u6821\u9A8C\u5339\u914D',
  exports: '\u5BFC\u51FA\u7ED3\u679C',
  employees: '\u5458\u5DE5\u4E3B\u6863',
  'data-management': '\u6570\u636E\u7BA1\u7406',
  'audit-logs': '\u5BA1\u8BA1\u65E5\u5FD7',
  employee: '\u5458\u5DE5',
  query: '\u81EA\u52A9\u67E5\u8BE2',
  workspace: '\u5DE5\u4F5C\u533A',
  admin: '\u7BA1\u7406\u5458',
  hr: 'HR',
  new: '\u65B0\u5EFA',
};

function buildBreadcrumbItems(pathname: string) {
  const segments = pathname.split('/').filter(Boolean);
  const items = [{ title: '\u9996\u9875' }];
  for (const seg of segments) {
    items.push({ title: LABEL_MAP[seg] || seg });
  }
  return items;
}

function AnimatedContent({ children }: PropsWithChildren) {
  const location = useLocation();
  const [show, setShow] = useState(true);
  const prevPath = useRef(location.pathname);

  useEffect(() => {
    if (prevPath.current !== location.pathname) {
      prevPath.current = location.pathname;
      setShow(false);
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          setShow(true);
        });
      });
    }
  }, [location.pathname]);

  return (
    <div className={show ? animations.pageEnterActive : animations.pageEnter}>
      {children}
    </div>
  );
}

function AggregateBanner() {
  const aggregateSession = useAggregateSession();
  const { lastError, clearError } = useApiFeedback();

  const aggregateMessage = aggregateSession.progress
    ? `${aggregateSession.progress.percent}% | ${aggregateSession.progress.label} | ${aggregateSession.progress.message}`
    : aggregateSession.error;

  return (
    <>
      {aggregateSession.status === 'running' && (
        <Alert
          type="info"
          banner
          message="\u5FEB\u901F\u805A\u5408\u6B63\u5728\u540E\u53F0\u8FD0\u884C"
          description={aggregateMessage}
          action={
            <Space>
              <Link to="/">\u56DE\u5230\u805A\u5408\u9875</Link>
              <Button size="small" onClick={cancelAggregateSession}>
                \u53D6\u6D88\u805A\u5408
              </Button>
            </Space>
          }
        />
      )}
      {aggregateSession.status !== 'idle' && aggregateSession.status !== 'running' && aggregateSession.progress && (
        <Alert
          type="success"
          banner
          message="\u5FEB\u901F\u805A\u5408\u8BB0\u5F55\u5DF2\u4FDD\u7559"
          description={aggregateMessage}
          action={
            <Space>
              <Link to="/">\u56DE\u5230\u805A\u5408\u9875</Link>
              <Button size="small" onClick={clearAggregateSession}>
                \u6E05\u9664\u8BB0\u5F55
              </Button>
            </Space>
          }
        />
      )}
      {lastError && (
        <Alert
          type="error"
          banner
          closable
          message={lastError.code ?? 'request_error'}
          description={lastError.message}
          onClose={clearError}
        />
      )}
    </>
  );
}

export function MainLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '\u9000\u51FA\u767B\u5F55',
      onClick: logout,
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        theme="dark"
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        width={220}
        collapsedWidth={64}
      >
        <div className={collapsed ? styles.logoCollapsed : styles.logo}>
          {collapsed ? '\u793E\u4FDD' : '\u793E\u4FDD\u516C\u79EF\u91D1\u7BA1\u7406\u7CFB\u7EDF'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={buildMenuItems(user?.role || '')}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: '#fff',
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #DEE0E3',
          }}
        >
          <Breadcrumb items={buildBreadcrumbItems(location.pathname)} />
          <Space>
            <span>{user?.displayName || '\u672A\u767B\u5F55'}</span>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Button type="text" icon={<UserOutlined />} />
            </Dropdown>
          </Space>
        </Header>
        <Content
          style={{
            margin: '0',
            padding: '24px',
            background: '#F5F6F7',
            minHeight: 'calc(100vh - 56px)',
          }}
        >
          <AggregateBanner />
          <AnimatedContent>
            <Outlet />
          </AnimatedContent>
        </Content>
      </Layout>
    </Layout>
  );
}
