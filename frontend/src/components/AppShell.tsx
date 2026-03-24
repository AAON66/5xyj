import { NavLink, useLocation } from 'react-router-dom';
import type { PropsWithChildren } from 'react';

import { getApiBaseUrl } from '../config/env';
import { formatApiBaseUrl } from '../utils';
import { GlobalFeedback } from './GlobalFeedback';

const navigationItems = [
  { to: '/', label: '系统门户', hint: '按管理员、HR、员工入口进入' },
  { to: '/workspace/admin', label: '管理员工作台', hint: '查看全链路入口与治理工具' },
  { to: '/workspace/hr', label: 'HR 工作台', hint: '聚焦导入、校验、导出与主档' },
  { to: '/employee/query', label: '员工查询', hint: '免登录按姓名和身份证查询' },
  { to: '/aggregate', label: '快速聚合', hint: '上传后自动输出双模板' },
  { to: '/dashboard', label: '处理看板', hint: '查看总览与最近批次' },
  { to: '/compare', label: '月度对比', hint: '左右分栏查看差异并在线修改' },
  { to: '/imports', label: '批次管理', hint: '保留完整解析钻取能力' },
  { to: '/mappings', label: '映射修正', hint: '处理低置信度表头映射' },
  { to: '/results', label: '校验匹配', hint: '查看问题与工号匹配结果' },
  { to: '/exports', label: '导出结果', hint: '检查两份固定模板产物' },
  { to: '/employees', label: '员工主档', hint: '导入、维护与审计主数据' },
];

export function AppShell({ children }: PropsWithChildren) {
  const location = useLocation();

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="app-sidebar__inner">
        <div>
            <p className="app-kicker">Social Security & Housing Fund Management</p>
            <h1 className="app-brand">社保公积金管理系统</h1>
            <p className="app-tagline">
              保留原有导入、识别、校验、匹配、对比和双模板导出能力，并增加管理员、HR 与员工自助查询分级入口。
            </p>
          </div>
          <nav className="app-nav" aria-label="主导航">
            {navigationItems.map((item) => (
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
