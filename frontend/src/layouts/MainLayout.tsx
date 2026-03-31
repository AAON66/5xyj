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
  { key: '/aggregate', icon: <UploadOutlined />, label: '快速融合', roles: ['admin', 'hr'] },
  { key: '/dashboard', icon: <DashboardOutlined />, label: '处理看板', roles: ['admin', 'hr'] },
  { key: '/compare', icon: <SwapOutlined />, label: '月度对比', roles: ['admin', 'hr'] },
  { key: '/imports', icon: <ImportOutlined />, label: '批次管理', roles: ['admin', 'hr'] },
  { key: '/mappings', icon: <ToolOutlined />, label: '映射修正', roles: ['admin', 'hr'] },
  { key: '/results', icon: <CheckCircleOutlined />, label: '校验匹配', roles: ['admin', 'hr'] },
  { key: '/exports', icon: <ExportOutlined />, label: '导出结果', roles: ['admin', 'hr'] },
  { key: '/employees', icon: <TeamOutlined />, label: '员工主档', roles: ['admin', 'hr'] },
  { key: '/data-management', icon: <DatabaseOutlined />, label: '数据管理', roles: ['admin', 'hr'] },
  { key: '/audit-logs', icon: <AuditOutlined />, label: '审计日志', roles: ['admin'] },
  { key: '/employee/query', icon: <SearchOutlined />, label: '员工查询', roles: ['employee'] },
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
  aggregate: '快速融合',
  dashboard: '处理看板',
  compare: '月度对比',
  imports: '批次管理',
  mappings: '映射修正',
  results: '校验匹配',
  exports: '导出结果',
  employees: '员工主档',
  'data-management': '数据管理',
  'audit-logs': '审计日志',
  employee: '员工',
  query: '自助查询',
  workspace: '工作区',
  admin: '管理员',
  hr: 'HR',
  new: '新建',
};

function useResponsiveCollapse(breakpoint: number = 1440): boolean {
  const [shouldCollapse, setShouldCollapse] = useState(
    () => typeof window !== 'undefined' && window.innerWidth <= breakpoint
  );

  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${breakpoint}px)`);
    const handler = (e: MediaQueryListEvent) => setShouldCollapse(e.matches);
    mql.addEventListener('change', handler);
    setShouldCollapse(mql.matches);
    return () => mql.removeEventListener('change', handler);
  }, [breakpoint]);

  return shouldCollapse;
}

function buildBreadcrumbItems(pathname: string) {
  const segments = pathname.split('/').filter(Boolean);
  const items = [{ title: '首页' }];
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
          message="快速聚合正在后台运行"
          description={aggregateMessage}
          action={
            <Space>
              <Link to="/">回到聚合页</Link>
              <Button size="small" onClick={cancelAggregateSession}>
                取消聚合
              </Button>
            </Space>
          }
        />
      )}
      {aggregateSession.status !== 'idle' && aggregateSession.status !== 'running' && aggregateSession.progress && (
        <Alert
          type="success"
          banner
          message="快速聚合记录已保留"
          description={aggregateMessage}
          action={
            <Space>
              <Link to="/">回到聚合页</Link>
              <Button size="small" onClick={clearAggregateSession}>
                清除记录
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

  const autoCollapsed = useResponsiveCollapse(1440);
  const [manualCollapse, setManualCollapse] = useState<boolean | null>(null);
  const prevAutoCollapsed = useRef(autoCollapsed);

  // When breakpoint changes, reset manual override so auto-collapse takes effect
  useEffect(() => {
    if (prevAutoCollapsed.current !== autoCollapsed) {
      prevAutoCollapsed.current = autoCollapsed;
      setManualCollapse(null);
    }
  }, [autoCollapsed]);

  const collapsed = manualCollapse !== null ? manualCollapse : autoCollapsed;

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: logout,
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        theme="dark"
        collapsible
        collapsed={collapsed}
        onCollapse={(value) => setManualCollapse(value)}
        width={220}
        collapsedWidth={64}
      >
        <div className={collapsed ? styles.logoCollapsed : styles.logo}>
          {collapsed ? '社保' : '社保公积金管理系统'}
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
            <span>{user?.displayName || '未登录'}</span>
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
            height: 'calc(100vh - 56px)',
            overflowY: 'auto',
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
