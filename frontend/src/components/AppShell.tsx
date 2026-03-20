import { NavLink, useLocation } from "react-router-dom";
import type { PropsWithChildren } from "react";

import { getApiBaseUrl } from "../config/env";
import { formatApiBaseUrl } from "../utils";
import { GlobalFeedback } from "./GlobalFeedback";

const navigationItems = [
  { to: "/", label: "看板", hint: "系统总览与状态检查" },
  { to: "/imports", label: "导入批次", hint: "上传入口与解析预览" },
  { to: "/employees", label: "员工主档", hint: "工号匹配前置数据" },
];

export function AppShell({ children }: PropsWithChildren) {
  const location = useLocation();

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="app-sidebar__inner">
          <div>
            <p className="app-kicker">Social Security Aggregation</p>
            <h1 className="app-brand">社保聚合</h1>
            <p className="app-tagline">
              先把多地区社保数据链路打通，再逐步补齐校验、匹配、导出和看板分析。
            </p>
          </div>
          <nav className="app-nav" aria-label="主导航">
            {navigationItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `app-nav__link${isActive ? " is-active" : ""}`}
              >
                <strong>{item.label}</strong>
                <span>{item.hint}</span>
              </NavLink>
            ))}
          </nav>
          <div className="app-sidebar__meta">
            <span>当前路由</span>
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
