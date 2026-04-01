import type { PropsWithChildren } from 'react';
import { NavLink, useLocation } from 'react-router-dom';

import { getApiBaseUrl } from '../config/env';
import { useAuth } from '../hooks';
import { formatApiBaseUrl } from '../utils';
import { GlobalFeedback } from './GlobalFeedback';

export function AppShell({ children }: PropsWithChildren) {
  const location = useLocation();
  const { user, logout } = useAuth();

  const navigationItems = [
    { to: '/aggregate', label: '快速融合', hint: '上传后直接触发融合、匹配和双模板导出。' },
    { to: '/dashboard', label: '处理看板', hint: '查看批次状态、异常分布与导出情况。' },
    { to: '/compare', label: '月度对比', hint: '按左右拆分差异视图查看并在线修正。' },
    { to: '/imports', label: '批次管理', hint: '查看原始文件、解析结果和处理详情。' },
    { to: '/mappings', label: '映射修正', hint: '处理低置信度字段映射与人工纠偏。' },
    { to: '/results', label: '校验匹配', hint: '查看校验问题和工号匹配结果。' },
    { to: '/exports', label: '导出结果', hint: '核对薪酬模板与工具表产物。' },
    { to: '/employees', label: '员工主档', hint: '导入、维护与审计员工主数据。' },
    { to: '/data-management', label: '数据管理', hint: '筛选、浏览和审计全量社保数据。', roles: ['admin', 'hr'] as string[] },
    { to: '/audit-logs', label: '审计日志', hint: '查看系统操作记录（仅管理员）。', adminOnly: true },
    { to: '/api-keys', label: 'API Key', hint: '创建和管理外部访问密钥（仅管理员）。', adminOnly: true },
    { to: '/employee/query', label: '员工查询', hint: '免登录员工自助查询入口。' },
  ];

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="app-sidebar__inner">
          <div>
            <p className="app-kicker">Social Security & Housing Fund Management</p>
            <h1 className="app-brand">社保公积金管理系统</h1>
            <p className="app-tagline">
              当前工作区已经启用登录校验。管理员和 HR 需要通过账号登录后进入系统，员工查询页保持免登录开放。
            </p>
          </div>

          <div className="app-sidebar__actions">
            <div className="app-sidebar__user">
              <span>当前登录</span>
              <strong>{user?.displayName || '未登录'}</strong>
              <small>{user?.username || '-'}</small>
            </div>
            <button type="button" className="app-sidebar__logout" onClick={logout}>
              退出登录
            </button>
          </div>

          <nav className="app-nav" aria-label="主导航">
            {navigationItems
              .filter((item) => {
                if (item.roles) return item.roles.includes(user?.role || '');
                if (item.adminOnly) return user?.role === 'admin';
                return true;
              })
              .map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `app-nav__link${isActive ? ' is-active' : ''}`}
              >
                <strong>{item.label}</strong>
                <span>{item.hint}</span>
              </NavLink>
            ))}
          </nav>

          <div className="app-sidebar__meta">
            <span>当前页面</span>
            <strong>{location.pathname}</strong>
            <span>访问模式</span>
            <strong>{user ? `${user.displayName} 已登录` : '未登录'}</strong>
            <span>API</span>
            <strong>{formatApiBaseUrl(getApiBaseUrl())}</strong>
          </div>
        </div>
      </aside>

      <div className="app-main">
        <GlobalFeedback />
        <main className="app-content">{children}</main>
      </div>
    </div>
  );
}
