import { useState, useEffect, useRef, useMemo, type PropsWithChildren } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Layout,
  Menu,
  Breadcrumb,
  Button,
  Dropdown,
  Alert,
  Space,
  Input,
  Tooltip,
  Drawer,
  Typography,
} from 'antd';
import type { MenuProps } from 'antd';
import {
  AlertOutlined,
  AppstoreOutlined,
  BarChartOutlined,
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
  KeyOutlined,
  LockOutlined,
  LogoutOutlined,
  SearchOutlined,
  UserOutlined,
  CloudSyncOutlined,
  SettingOutlined,
  SunOutlined,
  MoonOutlined,
  MenuOutlined,
  CloseOutlined,
} from '@ant-design/icons';

import { useAuth } from '../hooks/useAuth';
import { useAggregateSession } from '../hooks/useAggregateSession';
import { useApiFeedback } from '../hooks/useApiFeedback';
import { useFeishuFeatureFlag } from '../hooks/useFeishuFeatureFlag';
import { useMenuOpenKeys } from '../hooks/useMenuOpenKeys';
import { useResponsiveViewport } from '../hooks/useResponsiveViewport';
import { useThemeMode } from '../theme/useThemeMode';
import { useSemanticColors } from '../theme/useSemanticColors';
import { cancelAggregateSession, clearAggregateSession } from '../services/aggregateSessionStore';
import { ChangePasswordModal } from '../components/ChangePasswordModal';
import animations from '../theme/animations.module.css';
import styles from './MainLayout.module.css';

const { Header, Sider, Content } = Layout;

interface NavItem {
  key: string;
  icon: React.ReactNode;
  label: string;
  roles: string[];
}

interface MenuGroupConfig {
  key: string;
  label: string;
  icon: React.ReactNode;
  children: NavItem[];
  defaultOpen: boolean;
}

const TOP_ITEM: NavItem = { key: '/aggregate', icon: <UploadOutlined />, label: '快速融合', roles: ['admin', 'hr'] };

const MENU_GROUPS: MenuGroupConfig[] = [
  {
    key: 'group-common',
    label: '常用',
    icon: <AppstoreOutlined />,
    defaultOpen: true,
    children: [
      { key: '/dashboard', icon: <DashboardOutlined />, label: '处理看板', roles: ['admin', 'hr'] },
      { key: '/imports', icon: <ImportOutlined />, label: '批次管理', roles: ['admin', 'hr'] },
      { key: '/results', icon: <CheckCircleOutlined />, label: '校验匹配', roles: ['admin', 'hr'] },
      { key: '/exports', icon: <ExportOutlined />, label: '导出结果', roles: ['admin', 'hr'] },
    ],
  },
  {
    key: 'group-analysis',
    label: '数据分析',
    icon: <BarChartOutlined />,
    defaultOpen: false,
    children: [
      { key: '/compare', icon: <SwapOutlined />, label: '月度对比', roles: ['admin', 'hr'] },
      { key: '/period-compare', icon: <SwapOutlined />, label: '跨期对比', roles: ['admin', 'hr'] },
      { key: '/anomaly-detection', icon: <AlertOutlined />, label: '异常检测', roles: ['admin', 'hr'] },
      { key: '/mappings', icon: <ToolOutlined />, label: '映射修正', roles: ['admin', 'hr'] },
    ],
  },
  {
    key: 'group-admin',
    label: '管理',
    icon: <SettingOutlined />,
    defaultOpen: false,
    children: [
      { key: '/users', icon: <UserOutlined />, label: '账号管理', roles: ['admin'] },
      { key: '/employees', icon: <TeamOutlined />, label: '员工主档', roles: ['admin', 'hr'] },
      { key: '/data-management', icon: <DatabaseOutlined />, label: '数据管理', roles: ['admin', 'hr'] },
      { key: '/audit-logs', icon: <AuditOutlined />, label: '审计日志', roles: ['admin'] },
      { key: '/api-keys', icon: <KeyOutlined />, label: 'API 密钥', roles: ['admin'] },
      { key: '/settings', icon: <SettingOutlined />, label: '系统设置', roles: ['admin', 'hr'] },
    ],
  },
];

function resolveSelectedMenuKey(pathname: string): string {
  if (pathname.startsWith('/imports/')) return '/imports';
  if (pathname.startsWith('/employees/')) return '/employees';
  if (pathname.startsWith('/feishu-mapping/')) return '/feishu-settings';
  return pathname;
}

function findParentGroupKey(menuKey: string, groups: MenuGroupConfig[], feishuItems: NavItem[]): string | null {
  for (const group of groups) {
    const allChildren = group.key === 'group-admin'
      ? [...group.children, ...feishuItems]
      : group.children;
    if (allChildren.some((child) => child.key === menuKey)) {
      return group.key;
    }
  }
  return null;
}

function buildMenuItems(
  topItem: NavItem,
  groups: MenuGroupConfig[],
  feishuItems: NavItem[],
  userRole: string,
): MenuProps['items'] {
  if (userRole === 'employee') {
    return [{ key: '/employee/query', icon: <SearchOutlined />, label: '员工查询' }];
  }

  const items: MenuProps['items'] = [];

  if (topItem.roles.includes(userRole)) {
    items.push({ key: topItem.key, icon: topItem.icon, label: topItem.label });
  }

  for (const group of groups) {
    let groupChildren = [...group.children];
    if (group.key === 'group-admin' && feishuItems.length > 0) {
      groupChildren = [...groupChildren, ...feishuItems];
    }

    const visibleChildren = groupChildren
      .filter((child) => child.roles.includes(userRole))
      .map((child) => ({ key: child.key, icon: child.icon, label: child.label }));

    if (visibleChildren.length > 0) {
      items.push({
        key: group.key,
        icon: group.icon,
        label: group.label,
        children: visibleChildren,
      });
    }
  }

  return items;
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
  'period-compare': '跨期对比',
  'anomaly-detection': '异常检测',
  'api-keys': 'API 密钥',
  'feishu-sync': '飞书同步',
  'feishu-settings': '飞书设置',
  'feishu-mapping': '字段映射',
  settings: '系统设置',
  users: '账号管理',
};

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
  const { isMobile, isTablet, isCompactDesktop, isDesktopWide } = useResponsiveViewport();
  const { feishu_sync_enabled } = useFeishuFeatureFlag();
  const { isDark, toggleMode } = useThemeMode();
  const colors = useSemanticColors();

  const feishuItems: NavItem[] = useMemo(() => (
    feishu_sync_enabled ? [
      { key: '/feishu-sync', icon: <CloudSyncOutlined />, label: '飞书同步', roles: ['admin', 'hr'] },
      { key: '/feishu-settings', icon: <SettingOutlined />, label: '飞书设置', roles: ['admin'] },
    ] : []
  ), [feishu_sync_enabled]);

  const visibleGroupKeys = useMemo(() => {
    const role = user?.role || '';
    if (role === 'employee') return [] as string[];
    return MENU_GROUPS
      .filter((group) => {
        let children = [...group.children];
        if (group.key === 'group-admin') children = [...children, ...feishuItems];
        return children.some((child) => child.roles.includes(role));
      })
      .map((group) => group.key);
  }, [user?.role, feishuItems]);

  const defaultOpenKeys = useMemo(
    () => MENU_GROUPS.filter((group) => group.defaultOpen).map((group) => group.key),
    [],
  );
  const { openKeys, onOpenChange } = useMenuOpenKeys(defaultOpenKeys, visibleGroupKeys);

  const resolvedKey = resolveSelectedMenuKey(location.pathname);

  useEffect(() => {
    const parentGroup = findParentGroupKey(resolvedKey, MENU_GROUPS, feishuItems);
    if (parentGroup && !openKeys.includes(parentGroup)) {
      onOpenChange([...openKeys, parentGroup]);
    }
  }, [resolvedKey]); // eslint-disable-line react-hooks/exhaustive-deps -- route change is the only intended trigger

  const [menuSearch, setMenuSearch] = useState('');
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const allNavItems = useMemo(() => {
    const role = user?.role || '';
    if (role === 'employee') {
      return [{ key: '/employee/query', icon: <SearchOutlined />, label: '员工查询', roles: ['employee'] }];
    }

    const items: NavItem[] = [];
    if (TOP_ITEM.roles.includes(role)) items.push(TOP_ITEM);
    for (const group of MENU_GROUPS) {
      let children = [...group.children];
      if (group.key === 'group-admin') children = [...children, ...feishuItems];
      for (const child of children) {
        if (child.roles.includes(role)) {
          items.push(child);
        }
      }
    }
    return items;
  }, [user?.role, feishuItems]);

  const menuItems = useMemo(() => {
    if (!menuSearch) {
      return buildMenuItems(TOP_ITEM, MENU_GROUPS, feishuItems, user?.role || '');
    }
    const term = menuSearch.toLowerCase();
    return allNavItems
      .filter((item) => item.label.toLowerCase().includes(term))
      .map((item) => ({ key: item.key, icon: item.icon, label: item.label }));
  }, [allNavItems, feishuItems, menuSearch, user?.role]);

  const autoCollapsed = isCompactDesktop;
  const [manualCollapse, setManualCollapse] = useState<boolean | null>(() => {
    try {
      const saved = localStorage.getItem('sider-collapsed');
      if (saved !== null) return JSON.parse(saved);
    } catch {
      /* ignore storage access failures */
    }
    return null;
  });
  const prevAutoCollapsed = useRef(autoCollapsed);

  useEffect(() => {
    if (prevAutoCollapsed.current !== autoCollapsed) {
      prevAutoCollapsed.current = autoCollapsed;
      setManualCollapse(null);
      try {
        localStorage.removeItem('sider-collapsed');
      } catch {
        /* ignore storage access failures */
      }
    }
  }, [autoCollapsed]);

  useEffect(() => {
    if (isMobile) {
      setMobileNavOpen(false);
    }
  }, [location.pathname, isMobile]);

  const collapsed = manualCollapse !== null ? manualCollapse : autoCollapsed;

  const handleCollapse = (value: boolean) => {
    setManualCollapse(value);
    try {
      localStorage.setItem('sider-collapsed', JSON.stringify(value));
    } catch {
      /* ignore storage access failures */
    }
  };

  const handleNavigate = (key: string) => {
    navigate(key);
    setMenuSearch('');
  };

  const [changePasswordOpen, setChangePasswordOpen] = useState(false);

  const changePasswordItem: MenuProps['items'] = user?.role !== 'employee' ? [
    {
      key: 'change-password',
      icon: <LockOutlined />,
      label: '修改密码',
      onClick: () => setChangePasswordOpen(true),
    },
    { type: 'divider' as const },
  ] : [];

  const userMenuItems: MenuProps['items'] = [
    ...changePasswordItem,
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: logout,
    },
  ];

  const breadcrumbItems = buildBreadcrumbItems(location.pathname);
  const pageTitle = allNavItems.find((item) => item.key === resolvedKey)?.label
    ?? breadcrumbItems[breadcrumbItems.length - 1]?.title
    ?? '社保公积金管理系统';

  const contentPadding = isMobile
    ? '12px 12px 16px'
    : (isTablet || isCompactDesktop)
      ? '16px'
      : isDesktopWide
        ? '24px'
        : '24px';

  const navSearch = collapsed && !isMobile ? (
    <Tooltip title="搜索功能" placement="right">
      <Button
        type="text"
        icon={<SearchOutlined style={{ color: 'rgba(255,255,255,0.65)' }} />}
        onClick={() => handleCollapse(false)}
        style={{ width: '100%' }}
      />
    </Tooltip>
  ) : (
    <Input
      className={isMobile ? styles.drawerSearch : undefined}
      placeholder="搜索功能..."
      prefix={(
        <SearchOutlined style={{ color: isMobile ? colors.TEXT_TERTIARY : 'rgba(255,255,255,0.45)' }} />
      )}
      allowClear
      value={menuSearch}
      onChange={(event) => setMenuSearch(event.target.value)}
      style={isMobile ? undefined : {
        background: 'rgba(255,255,255,0.08)',
        borderColor: 'rgba(255,255,255,0.15)',
        color: '#fff',
      }}
    />
  );

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {isMobile ? null : (
        <Sider
          theme="dark"
          collapsible
          collapsed={collapsed}
          onCollapse={handleCollapse}
          width={220}
          collapsedWidth={64}
        >
          <div className={collapsed ? styles.logoCollapsed : styles.logo}>
            {collapsed ? '社保' : '社保公积金管理系统'}
          </div>
          <div style={{ padding: collapsed ? '8px 12px' : '8px 16px' }}>
            {navSearch}
          </div>
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[resolvedKey]}
            openKeys={menuSearch ? [] : openKeys}
            onOpenChange={menuSearch ? undefined : onOpenChange}
            items={menuItems}
            onClick={({ key }) => {
              handleNavigate(String(key));
            }}
          />
        </Sider>
      )}
      <Layout>
        <Header
          style={{
            background: colors.BG_CONTAINER,
            padding: isMobile ? '0 12px' : '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: `1px solid ${colors.BORDER}`,
          }}
        >
          {isMobile ? (
            <div className={styles.mobileHeaderLeft}>
              <Button
                type="text"
                icon={<MenuOutlined />}
                aria-label="打开导航菜单"
                onClick={() => setMobileNavOpen(true)}
              />
              <Typography.Text className={styles.mobileHeaderTitle} strong ellipsis>
                {String(pageTitle)}
              </Typography.Text>
            </div>
          ) : (
            <Breadcrumb items={buildBreadcrumbItems(location.pathname)} />
          )}
          <Space>
            {isMobile ? null : <span>{user?.displayName || '未登录'}</span>}
            <Button
              type="text"
              icon={isDark ? <SunOutlined /> : <MoonOutlined />}
              onClick={toggleMode}
              aria-label={isDark ? '切换到亮色模式' : '切换到暗色模式'}
            />
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Button type="text" icon={<UserOutlined />} aria-label="打开用户菜单" />
            </Dropdown>
          </Space>
        </Header>
        <Content
          style={{
            margin: 0,
            padding: contentPadding,
            background: colors.BG_LAYOUT,
          }}
        >
          <AggregateBanner />
          <AnimatedContent>
            <Outlet />
          </AnimatedContent>
        </Content>
      </Layout>
      <Drawer
        placement="left"
        width="min(320px, 100vw)"
        open={mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
        closable={false}
        styles={{ body: { padding: 0 } }}
      >
        <div
          className={styles.drawerHeader}
          style={{ borderBottom: `1px solid ${colors.BORDER}` }}
        >
          <div className={styles.drawerHeaderTop}>
            <div className={styles.drawerBrand}>社保公积金管理系统</div>
            <Button
              type="text"
              icon={<CloseOutlined />}
              aria-label="关闭导航抽屉"
              onClick={() => setMobileNavOpen(false)}
            />
          </div>
          {navSearch}
        </div>
        <Menu
          selectedKeys={[resolvedKey]}
          openKeys={menuSearch ? [] : openKeys}
          onOpenChange={menuSearch ? undefined : onOpenChange}
          items={menuItems}
          onClick={({ key }) => {
            handleNavigate(String(key));
          }}
        />
      </Drawer>
      <ChangePasswordModal
        open={changePasswordOpen}
        forced={false}
        onSuccess={() => setChangePasswordOpen(false)}
        onCancel={() => setChangePasswordOpen(false)}
      />
      {user?.mustChangePassword && user?.role !== 'employee' && (
        <ChangePasswordModal
          open={true}
          forced={true}
          onSuccess={() => {
            // writeAuthSession already called inside Modal
            // AUTH_SESSION_EVENT dispatched -> AuthProvider syncs -> mustChangePassword becomes false
          }}
        />
      )}
    </Layout>
  );
}

export default MainLayout;
