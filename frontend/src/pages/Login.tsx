import { useState, type FormEvent } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../hooks';
import { normalizeApiError } from '../services/api';
import type { AuthRole } from '../services/authSession';

type LoginMode = 'credential' | 'employee';

const DEFAULT_WORKSPACE_BY_ROLE: Record<AuthRole, string> = {
  admin: '/workspace/admin',
  hr: '/workspace/hr',
  employee: '/employee/query',
};

const ROLE_OPTIONS: Array<{ role: Extract<AuthRole, 'admin' | 'hr'>; title: string; description: string }> = [
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
  const { isAuthenticated, isInitializing, user, login, verifyEmployee } = useAuth();

  const [loginMode, setLoginMode] = useState<LoginMode>('credential');

  // Credential login state
  const [role, setRole] = useState<Extract<AuthRole, 'admin' | 'hr'>>('admin');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // Employee verify state
  const [employeeId, setEmployeeId] = useState('');
  const [idNumber, setIdNumber] = useState('');
  const [personName, setPersonName] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [passwordWarning, setPasswordWarning] = useState(false);

  if (!isInitializing && isAuthenticated && user) {
    return <Navigate to={DEFAULT_WORKSPACE_BY_ROLE[user.role]} replace />;
  }

  async function handleCredentialSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setErrorMessage(null);
    setPasswordWarning(false);

    try {
      await login({
        username: username.trim(),
        password,
        role,
      });

      // Check must_change_password from session after login
      const session = window.localStorage.getItem('social-security-auth-session');
      if (session) {
        try {
          const parsed = JSON.parse(session);
          if (parsed.mustChangePassword) {
            setPasswordWarning(true);
            // Give user a moment to see the warning before navigating
            setTimeout(() => {
              navigate(resolveTargetPath(location, role), { replace: true });
            }, 2000);
            return;
          }
        } catch {
          // ignore parse errors
        }
      }

      navigate(resolveTargetPath(location, role), { replace: true });
    } catch (error) {
      setErrorMessage(normalizeApiError(error).message || '登录失败，请检查账号、密码和角色。');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleEmployeeSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setErrorMessage(null);

    try {
      await verifyEmployee({
        employee_id: employeeId.trim(),
        id_number: idNumber.trim(),
        person_name: personName.trim(),
      });
      navigate('/employee/query', { replace: true });
    } catch (error) {
      const apiError = normalizeApiError(error);
      // Handle rate limit (429)
      if (apiError.statusCode === 429) {
        setErrorMessage('验证失败次数过多，请15分钟后重试。');
      } else {
        setErrorMessage('身份验证失败，请检查工号、身份证号和姓名。');
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-shell">
      <section className="login-card">
        <div className="login-card__header">
          <p className="portal-kicker">Secure Access</p>
          <h1>{loginMode === 'credential' ? '管理员与 HR 登录' : '员工身份验证'}</h1>
          <p>
            {loginMode === 'credential'
              ? '系统已开启账号校验。管理员和 HR 页面需要登录后才能访问。'
              : '使用工号、身份证号和姓名验证身份，查看个人社保公积金信息。'}
          </p>
        </div>

        <div className="login-mode-tabs" role="tablist" aria-label="登录方式">
          <button
            type="button"
            role="tab"
            aria-selected={loginMode === 'credential'}
            className={`login-mode-tab${loginMode === 'credential' ? ' is-active' : ''}`}
            onClick={() => {
              setLoginMode('credential');
              setErrorMessage(null);
              setPasswordWarning(false);
            }}
          >
            管理员/HR 登录
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={loginMode === 'employee'}
            className={`login-mode-tab${loginMode === 'employee' ? ' is-active' : ''}`}
            onClick={() => {
              setLoginMode('employee');
              setErrorMessage(null);
              setPasswordWarning(false);
            }}
          >
            员工身份验证
          </button>
        </div>

        {loginMode === 'credential' ? (
          <>
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

            <form className="login-form" onSubmit={handleCredentialSubmit}>
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

              {passwordWarning ? (
                <div className="login-form__warning">当前密码为默认密码，请尽快修改。</div>
              ) : null}

              {errorMessage ? <div className="login-form__error">{errorMessage}</div> : null}

              <button className="login-card__submit" type="submit" disabled={submitting || !username.trim() || !password}>
                {submitting ? '登录中...' : '登录并进入工作台'}
              </button>
            </form>
          </>
        ) : (
          <form className="login-form" onSubmit={handleEmployeeSubmit}>
            <label>
              <span>工号</span>
              <input
                value={employeeId}
                onChange={(event) => setEmployeeId(event.target.value)}
                placeholder="请输入工号"
              />
            </label>
            <label>
              <span>身份证号</span>
              <input
                value={idNumber}
                onChange={(event) => setIdNumber(event.target.value)}
                placeholder="请输入身份证号"
              />
            </label>
            <label>
              <span>姓名</span>
              <input
                value={personName}
                onChange={(event) => setPersonName(event.target.value)}
                placeholder="请输入姓名"
              />
            </label>

            {errorMessage ? <div className="login-form__error">{errorMessage}</div> : null}

            <button
              className="login-card__submit"
              type="submit"
              disabled={submitting || !employeeId.trim() || !idNumber.trim() || !personName.trim()}
            >
              {submitting ? '验证中...' : '验证并进入'}
            </button>
          </form>
        )}

        <div className="login-card__footer">
          <span>员工自助查询仍可直接使用。</span>
          <Link to="/employee/query">进入员工查询</Link>
        </div>
      </section>
    </div>
  );
}
