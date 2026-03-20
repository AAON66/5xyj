import { NavLink } from "react-router-dom";
import type { PropsWithChildren } from "react";

export function AppShell({ children }: PropsWithChildren) {
  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <h1 className="app-brand">社保聚合</h1>
        <p className="app-tagline">
          先把多地区社保数据链路打通，再逐步补齐校验、匹配和双模板导出。
        </p>
        <nav className="app-nav">
          <NavLink to="/">看板</NavLink>
          <NavLink to="/imports">导入批次</NavLink>
          <NavLink to="/employees">员工主数据</NavLink>
        </nav>
      </aside>
      <main className="app-content">{children}</main>
    </div>
  );
}

