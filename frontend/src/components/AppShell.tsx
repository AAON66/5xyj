import { NavLink, useLocation } from 'react-router-dom';
import type { PropsWithChildren } from 'react';

import { getApiBaseUrl } from '../config/env';
import { formatApiBaseUrl } from '../utils';
import { GlobalFeedback } from './GlobalFeedback';

const navigationItems = [
  { to: '/', label: '\u5feb\u901f\u805a\u5408', hint: '\u4e0a\u4f20\u540e\u81ea\u52a8\u8f93\u51fa\u53cc\u6a21\u677f' },
  { to: '/dashboard', label: '\u5904\u7406\u770b\u677f', hint: '\u67e5\u770b\u603b\u89c8\u4e0e\u6700\u8fd1\u6279\u6b21' },
  { to: '/imports', label: '\u6279\u6b21\u7ba1\u7406', hint: '\u4fdd\u7559\u5b8c\u6574\u89e3\u6790\u94bb\u53d6\u80fd\u529b' },
  { to: '/mappings', label: '\u6620\u5c04\u4fee\u6b63', hint: '\u5904\u7406\u4f4e\u7f6e\u4fe1\u5ea6\u8868\u5934\u6620\u5c04' },
  { to: '/results', label: '\u6821\u9a8c\u5339\u914d', hint: '\u67e5\u770b\u95ee\u9898\u4e0e\u5de5\u53f7\u5339\u914d\u7ed3\u679c' },
  { to: '/exports', label: '\u5bfc\u51fa\u7ed3\u679c', hint: '\u68c0\u67e5\u4e24\u4efd\u56fa\u5b9a\u6a21\u677f\u4ea7\u7269' },
  { to: '/employees', label: '\u5458\u5de5\u4e3b\u6863', hint: '\u5bfc\u5165\u3001\u7ef4\u62a4\u4e0e\u5ba1\u8ba1\u4e3b\u6570\u636e' },
];

export function AppShell({ children }: PropsWithChildren) {
  const location = useLocation();

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="app-sidebar__inner">
          <div>
            <p className="app-kicker">Social Security Aggregation</p>
            <h1 className="app-brand">\u793e\u4fdd\u805a\u5408\u5de5\u5177</h1>
            <p className="app-tagline">
              \u9ed8\u8ba4\u4ece\u5feb\u901f\u805a\u5408\u5f00\u59cb\uff1a\u4e0a\u4f20\u793e\u4fdd\u6587\u4ef6\uff0c\u7cfb\u7edf\u81ea\u52a8\u5b8c\u6210\u89e3\u6790\u3001\u6821\u9a8c\u3001\u5339\u914d\u548c\u53cc\u6a21\u677f\u5bfc\u51fa\u3002
            </p>
          </div>
          <nav className="app-nav" aria-label="\u4e3b\u5bfc\u822a">
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
            <span>\u5f53\u524d\u9875\u9762</span>
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
