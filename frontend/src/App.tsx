import { Route, Routes } from "react-router-dom";

import { AppShell } from "./components";
import { DashboardPage, EmployeesPage, ExportsPage, ImportsPage, NotFoundPage, ResultsPage } from "./pages";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/imports" element={<ImportsPage />} />
        <Route path="/results" element={<ResultsPage />} />
        <Route path="/exports" element={<ExportsPage />} />
        <Route path="/employees" element={<EmployeesPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AppShell>
  );
}
