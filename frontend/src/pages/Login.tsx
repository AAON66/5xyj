import { useState, type FormEvent } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../hooks';
import { normalizeApiError } from '../services/api';
import type { AuthRole } from '../services/authSession';

const DEFAULT_WORKSPACE_BY_ROLE: Record<AuthRole, string> = {
  admin: '/workspace/admin',
  hr: '/workspace/hr',
};

const ROLE_OPTIONS: Array<{ role: AuthRole; title: string; description: string }> = [
  { role: 'admin', title: '管理员入口', description: '系统治理、批次管理、月度对比和模板核查。' },
  { role: 'hr', title: 'HR 入口', description: '月度处理、校验匹配、员工主档和导出复核。' },
];

function resolveTargetPath(location: ReturnType<typeof useLocation>, role: AuthRole): string {
  const from = (location.state as { from?: unknown } | null)?.from;
  return typeof from === 'string' && from.startsWith('/') ? from : DEFAULT_WORKSPACE_BY_ROLE[role];
}

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, isInitializing, user, login } = useAuth();
  const [role, setRole] = useState<AuthRole>('admin');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isInitializing && isAuthenticated && user) {
    return <Navigate to={DEFAULT_WORKSPACE_BY_ROLE[user.role]} replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setErrorMessage(null);

    try {
      await login({
        username: username.trim(),
        password,
        role,
      });
      navigate(resolveTargetPath(location, role), { replace: true });
    } catch (error) {
      setErrorMessage(normalizeApiError(error).message || '登录失败，请检查账号、密码和角色。');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-shell">
      <section className="login-card">
        <div className="login-card__header">
          <p className="portal-kicker">Secure Access</p>
          <h1>管理员与 HR 登录</h1>
          <p>系统已开启账号校验。管理员和 HR 页面需要登录后才能访问，员工查询入口仍保持免登录。</p>
        </div>

        <div className="login-role-grid" role="tablist" aria-label="登录角色">
          {ROLE_OPTIONS.map((item) => (
            <button
              key={item.role}
              type="button"
              className={`login-role-card${role === item.role ? ' is-active' : ''}`}
              onClick={() => setRole(item.role)}
            >
              <strong>{item.title}</strong>
              <span>{item.description}</span>
            </button>
          ))}
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label>
            <span>账号</span>
            <input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="请输入系统账号" />
          </label>
          <label>
            <span>密码</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="请输入密码"
            />
          </label>

          {errorMessage ? <div className="login-form__error">{errorMessage}</div> : null}

          <button className="login-card__submit" type="submit" disabled={submitting || !username.trim() || !password}>
            {submitting ? '登录中...' : '登录并进入工作台'}
          </button>
        </form>

        <div className="login-card__footer">
          <span>员工自助查询仍可直接使用。</span>
          <Link to="/employee/query">进入员工查询</Link>
        </div>
      </section>
    </div>
  );
}
