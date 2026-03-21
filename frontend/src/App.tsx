import { Route, Routes } from "react-router-dom";

import { AppShell } from "./components";
import { DashboardPage, EmployeesPage, ExportsPage, ImportBatchDetailPage, ImportsPage, MappingsPage, NotFoundPage, ResultsPage, SimpleAggregatePage } from "./pages";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<SimpleAggregatePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
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
