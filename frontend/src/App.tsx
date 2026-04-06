import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom';
import { Spin } from 'antd';

import { MainLayout } from './layouts/MainLayout';
import { useAuth } from './hooks';
import { useSemanticColors } from './theme/useSemanticColors';
import {
  AdminWorkspacePage,
  AnomalyDetectionPage,
  ApiKeysPage,
  AuditLogsPage,
  ComparePage,
  EmployeeCreatePage,
  DashboardPage,
  DataManagementPage,
  EmployeeSelfServicePage,
  EmployeesPage,
  ExportsPage,
  FeishuFieldMappingPage,
  FeishuSettingsPage,
  FeishuSyncPage,
  HrWorkspacePage,
  ImportBatchDetailPage,
  ImportsPage,
  LoginPage,
  MappingsPage,
  NotFoundPage,
  PeriodComparePage,
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
  const colors = useSemanticColors();
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: colors.BG_LAYOUT }}>
      <Spin tip={message} size="large"><div style={{ padding: 50 }} /></Spin>
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
  return <MainLayout />;
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
          <Route element={<RoleRoute allowedRoles={['admin', 'hr']} />}>
            <Route path="/workspace/hr" element={<HrWorkspacePage />} />
            <Route path="/aggregate" element={<SimpleAggregatePage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="/period-compare" element={<PeriodComparePage />} />
            <Route path="/anomaly-detection" element={<AnomalyDetectionPage />} />
            <Route path="/imports" element={<ImportsPage />} />
            <Route path="/imports/:batchId" element={<ImportBatchDetailPage />} />
            <Route path="/mappings" element={<MappingsPage />} />
            <Route path="/results" element={<ResultsPage />} />
            <Route path="/exports" element={<ExportsPage />} />
            <Route path="/employees/new" element={<EmployeeCreatePage />} />
            <Route path="/employees" element={<EmployeesPage />} />
            <Route path="/data-management" element={<DataManagementPage />} />
            <Route path="/feishu-sync" element={<FeishuSyncPage />} />
          </Route>
          <Route element={<RoleRoute allowedRoles={['admin']} />}>
            <Route path="/workspace/admin" element={<AdminWorkspacePage />} />
            <Route path="/audit-logs" element={<AuditLogsPage />} />
            <Route path="/api-keys" element={<ApiKeysPage />} />
            <Route path="/feishu-settings" element={<FeishuSettingsPage />} />
            <Route path="/feishu-mapping/:configId" element={<FeishuFieldMappingPage />} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
