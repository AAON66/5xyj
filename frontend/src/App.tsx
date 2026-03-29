import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom';

import { AppShell } from './components';
import { useAuth } from './hooks';
import {
  AdminWorkspacePage,
  AuditLogsPage,
  ComparePage,
  EmployeeCreatePage,
  DashboardPage,
  EmployeeSelfServicePage,
  EmployeesPage,
  ExportsPage,
  HrWorkspacePage,
  ImportBatchDetailPage,
  ImportsPage,
  LoginPage,
  MappingsPage,
  NotFoundPage,
  ResultsPage,
  SimpleAggregatePage,
} from './pages';
import type { AuthRole } from './services/authSession';

const DEFAULT_WORKSPACE_BY_ROLE: Record<AuthRole, string> = {
  admin: '/workspace/admin',
  hr: '/workspace/hr',
  employee: '/employee/query',
};

function AuthRouteState({ message }: { message: string }) {
  return (
    <div className="auth-route-state">
      <div className="auth-route-state__card">
        <p className="portal-kicker">Secure Access</p>
        <strong>{message}</strong>
      </div>
    </div>
  );
}

function RootRedirect() {
  const { isAuthenticated, isInitializing, user } = useAuth();

  if (isInitializing) {
    return <AuthRouteState message="正在校验登录状态..." />;
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  return <Navigate to={DEFAULT_WORKSPACE_BY_ROLE[user.role]} replace />;
}

function PublicOnlyRoute() {
  const { isAuthenticated, isInitializing, user } = useAuth();

  if (isInitializing) {
    return <AuthRouteState message="正在校验登录状态..." />;
  }

  if (isAuthenticated && user) {
    return <Navigate to={DEFAULT_WORKSPACE_BY_ROLE[user.role]} replace />;
  }

  return <Outlet />;
}

function ProtectedRoute() {
  const location = useLocation();
  const { isAuthenticated, isInitializing } = useAuth();

  if (isInitializing) {
    return <AuthRouteState message="正在进入安全工作区..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: `${location.pathname}${location.search}${location.hash}` }} />;
  }

  return <Outlet />;
}

function RoleRoute({ allowedRoles }: { allowedRoles: AuthRole[] }) {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(user.role)) {
    return <Navigate to={DEFAULT_WORKSPACE_BY_ROLE[user.role]} replace />;
  }

  return <Outlet />;
}

function ProtectedLayout() {
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />
      <Route element={<PublicOnlyRoute />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<ProtectedLayout />}>
          <Route element={<RoleRoute allowedRoles={['employee']} />}>
            <Route path="/employee/query" element={<EmployeeSelfServicePage />} />
          </Route>
          <Route element={<RoleRoute allowedRoles={['admin']} />}>
            <Route path="/workspace/admin" element={<AdminWorkspacePage />} />
            <Route path="/audit-logs" element={<AuditLogsPage />} />
          </Route>
          <Route path="/workspace/hr" element={<HrWorkspacePage />} />
          <Route path="/aggregate" element={<SimpleAggregatePage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/imports" element={<ImportsPage />} />
          <Route path="/imports/:batchId" element={<ImportBatchDetailPage />} />
          <Route path="/mappings" element={<MappingsPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/exports" element={<ExportsPage />} />
          <Route path="/employees/new" element={<EmployeeCreatePage />} />
          <Route path="/employees" element={<EmployeesPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
