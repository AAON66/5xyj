import { Route, Routes } from "react-router-dom";

import { AppShell } from "./components";
import { DashboardPage, EmployeesPage, ImportsPage, NotFoundPage, ResultsPage } from "./pages";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/imports" element={<ImportsPage />} />
        <Route path="/results" element={<ResultsPage />} />
        <Route path="/employees" element={<EmployeesPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AppShell>
  );
}
