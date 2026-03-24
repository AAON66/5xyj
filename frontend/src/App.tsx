import { Route, Routes, useLocation } from 'react-router-dom';

import { AppShell } from './components';
import { AdminWorkspacePage, ComparePage, DashboardPage, EmployeeSelfServicePage, EmployeesPage, ExportsPage, HrWorkspacePage, ImportBatchDetailPage, ImportsPage, ManagementPortalPage, MappingsPage, NotFoundPage, ResultsPage, SimpleAggregatePage } from './pages';

function PublicRoutes() {
  return (
    <Routes>
      <Route path="/" element={<ManagementPortalPage />} />
      <Route path="/workspace/admin" element={<AdminWorkspacePage />} />
      <Route path="/workspace/hr" element={<HrWorkspacePage />} />
      <Route path="/employee/query" element={<EmployeeSelfServicePage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

function ManagedRoutes() {
  return (
    <AppShell>
      <Routes>
        <Route path="/aggregate" element={<SimpleAggregatePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/compare" element={<ComparePage />} />
        <Route path="/imports" element={<ImportsPage />} />
        <Route path="/imports/:batchId" element={<ImportBatchDetailPage />} />
        <Route path="/mappings" element={<MappingsPage />} />
        <Route path="/results" element={<ResultsPage />} />
        <Route path="/exports" element={<ExportsPage />} />
        <Route path="/employees" element={<EmployeesPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AppShell>
  );
}

export default function App() {
  const location = useLocation();
  const isPublicRoute =
    location.pathname === '/' ||
    location.pathname.startsWith('/workspace/') ||
    location.pathname.startsWith('/employee/query');

  return isPublicRoute ? <PublicRoutes /> : <ManagedRoutes />;
}
