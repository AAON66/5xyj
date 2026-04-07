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
  LogoutOutlined,
  SearchOutlined,
  UserOutlined,
  CloudSyncOutlined,
  SettingOutlined,
  SunOutlined,
  MoonOutlined,
} from '@ant-design/icons';

import { useAuth } from '../hooks/useAuth';
import { useAggregateSession } from '../hooks/useAggregateSession';
import { useApiFeedback } from '../hooks/useApiFeedback';
import { useFeishuFeatureFlag } from '../hooks/useFeishuFeatureFlag';
import { useMenuOpenKeys } from '../hooks/useMenuOpenKeys';
import { useThemeMode } from '../theme/useThemeMode';
import { useSemanticColors } from '../theme/useSemanticColors';
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
      { key: '/employees', icon: <TeamOutlined />, label: '员工主档', roles: ['admin', 'hr'] },
      { key: '/data-management', icon: <DatabaseOutlined />, label: '数据管理', roles: ['admin', 'hr'] },
      { key: '/audit-logs', icon: <AuditOutlined />, label: '审计日志', roles: ['admin'] },
      { key: '/api-keys', icon: <KeyOutlined />, label: 'API 密钥', roles: ['admin'] },
      { key: '/settings', icon: <SettingOutlined />, label: '系统设置', roles: ['admin', 'hr'] },
    ],
  },
];

/** Map detail/sub-routes back to their parent menu key for selectedKeys highlight */
function resolveSelectedMenuKey(pathname: string): string {
  if (pathname.startsWith('/imports/')) return '/imports';
  if (pathname.startsWith('/employees/')) return '/employees';
  if (pathname.startsWith('/feishu-mapping/')) return '/feishu-settings';
  return pathname;
}

/** Find which group contains the given menu key, used to auto-expand parent group */
function findParentGroupKey(menuKey: string, groups: MenuGroupConfig[], feishuItems: NavItem[]): string | null {
  for (const group of groups) {
    const allChildren = group.key === 'group-admin'
      ? [...group.children, ...feishuItems]
      : group.children;
    if (allChildren.some(child => child.key === menuKey)) {
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
  // Employee role: no groups, single item only
  if (userRole === 'employee') {
    return [{ key: '/employee/query', icon: <SearchOutlined />, label: '员工查询' }];
  }

  const items: MenuProps['items'] = [];

  // Top pinned item
  if (topItem.roles.includes(userRole)) {
    items.push({ key: topItem.key, icon: topItem.icon, label: topItem.label });
  }

  // Grouped SubMenus
  for (const group of groups) {
    let groupChildren = [...group.children];
    if (group.key === 'group-admin' && feishuItems.length > 0) {
      groupChildren = [...groupChildren, ...feishuItems];
    }

    const visibleChildren = groupChildren
      .filter(child => child.roles.includes(userRole))
      .map(child => ({ key: child.key, icon: child.icon, label: child.label }));

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
  const { feishu_sync_enabled } = useFeishuFeatureFlag();
  const { isDark, toggleMode } = useThemeMode();
  const colors = useSemanticColors();

  // Feishu menu items conditionally injected into admin group
  const feishuItems: NavItem[] = useMemo(() =>
    feishu_sync_enabled ? [
      { key: '/feishu-sync', icon: <CloudSyncOutlined />, label: '飞书同步', roles: ['admin', 'hr'] },
      { key: '/feishu-settings', icon: <SettingOutlined />, label: '飞书设置', roles: ['admin'] },
    ] : [],
    [feishu_sync_enabled]
  );

  // Compute visible group keys for validKeys cleanup in useMenuOpenKeys
  const visibleGroupKeys = useMemo(() => {
    const role = user?.role || '';
    if (role === 'employee') return [] as string[];
    return MENU_GROUPS
      .filter(g => {
        let children = [...g.children];
        if (g.key === 'group-admin') children = [...children, ...feishuItems];
        return children.some(c => c.roles.includes(role));
      })
      .map(g => g.key);
  }, [user?.role, feishuItems]);

  const defaultOpenKeys = useMemo(
    () => MENU_GROUPS.filter(g => g.defaultOpen).map(g => g.key),
    []
  );
  const { openKeys, onOpenChange } = useMenuOpenKeys(defaultOpenKeys, visibleGroupKeys);

  // Resolve sub-routes to parent menu key for correct highlight
  const resolvedKey = resolveSelectedMenuKey(location.pathname);

  // Auto-expand parent group when navigating to a child item
  useEffect(() => {
    const parentGroup = findParentGroupKey(resolvedKey, MENU_GROUPS, feishuItems);
    if (parentGroup && !openKeys.includes(parentGroup)) {
      onOpenChange([...openKeys, parentGroup]);
    }
  }, [resolvedKey]); // eslint-disable-line react-hooks/exhaustive-deps -- only trigger on route change

  // Global menu search
  const [menuSearch, setMenuSearch] = useState('');

  // Collect all searchable items (flat list for search filtering)
  const allNavItems = useMemo(() => {
    const role = user?.role || '';
    if (role === 'employee') return [{ key: '/employee/query', icon: <SearchOutlined />, label: '员工查询', roles: ['employee'] }];
    const items: NavItem[] = [];
    if (TOP_ITEM.roles.includes(role)) items.push(TOP_ITEM);
    for (const group of MENU_GROUPS) {
      let children = [...group.children];
      if (group.key === 'group-admin') children = [...children, ...feishuItems];
      for (const child of children) {
        if (child.roles.includes(role)) items.push(child);
      }
    }
    return items;
  }, [user?.role, feishuItems]);

  // Build grouped menu items (normal mode) or flat filtered list (search mode)
  const menuItems = useMemo(() => {
    if (!menuSearch) {
      return buildMenuItems(TOP_ITEM, MENU_GROUPS, feishuItems, user?.role || '');
    }
    const term = menuSearch.toLowerCase();
    return allNavItems
      .filter(item => item.label.toLowerCase().includes(term))
      .map(item => ({ key: item.key, icon: item.icon, label: item.label }));
  }, [feishuItems, user?.role, menuSearch, allNavItems]);

  const autoCollapsed = useResponsiveCollapse(1440);
  const [manualCollapse, setManualCollapse] = useState<boolean | null>(() => {
    try {
      const saved = localStorage.getItem('sider-collapsed');
      if (saved !== null) return JSON.parse(saved);
    } catch { /* ignore */ }
    return null;
  });
  const prevAutoCollapsed = useRef(autoCollapsed);

  // When breakpoint changes, reset manual override so auto-collapse takes effect
  useEffect(() => {
    if (prevAutoCollapsed.current !== autoCollapsed) {
      prevAutoCollapsed.current = autoCollapsed;
      setManualCollapse(null);
      try { localStorage.removeItem('sider-collapsed'); } catch { /* ignore */ }
    }
  }, [autoCollapsed]);

  const collapsed = manualCollapse !== null ? manualCollapse : autoCollapsed;

  // Persist sider collapsed state
  const handleCollapse = (value: boolean) => {
    setManualCollapse(value);
    try { localStorage.setItem('sider-collapsed', JSON.stringify(value)); } catch { /* ignore */ }
  };

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
        onCollapse={handleCollapse}
        width={220}
        collapsedWidth={64}
      >
        <div className={collapsed ? styles.logoCollapsed : styles.logo}>
          {collapsed ? '社保' : '社保公积金管理系统'}
        </div>
        <div style={{ padding: collapsed ? '8px 12px' : '8px 16px' }}>
          {collapsed ? (
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
              placeholder="搜索功能..."
              prefix={<SearchOutlined style={{ color: 'rgba(255,255,255,0.45)' }} />}
              allowClear
              value={menuSearch}
              onChange={e => setMenuSearch(e.target.value)}
              style={{
                background: 'rgba(255,255,255,0.08)',
                borderColor: 'rgba(255,255,255,0.15)',
                color: '#fff',
              }}
            />
          )}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[resolvedKey]}
          openKeys={menuSearch ? [] : openKeys}
          onOpenChange={menuSearch ? undefined : onOpenChange}
          items={menuItems}
          onClick={({ key }) => { navigate(key); setMenuSearch(''); }}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: colors.BG_CONTAINER,
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: `1px solid ${colors.BORDER}`,
          }}
        >
          <Breadcrumb items={buildBreadcrumbItems(location.pathname)} />
          <Space>
            <span>{user?.displayName || '未登录'}</span>
            <Button
              type="text"
              icon={isDark ? <SunOutlined /> : <MoonOutlined />}
              onClick={toggleMode}
              aria-label={isDark ? '切换到亮色模式' : '切换到暗色模式'}
            />
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Button type="text" icon={<UserOutlined />} />
            </Dropdown>
          </Space>
        </Header>
        <Content
          style={{
            margin: '0',
            padding: '24px',
            background: colors.BG_LAYOUT,
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
