import React, { useMemo } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ConfigProvider, App as AntApp } from "antd";
import zhCN from "antd/locale/zh_CN";

import App from "./App";
import { ApiFeedbackProvider, AuthProvider } from "./components";
import { ThemeModeProvider } from "./theme/ThemeModeProvider";
import { useThemeMode } from "./theme/useThemeMode";
import { buildTheme } from "./theme";

function ThemedConfig({ children }: { children: React.ReactNode }) {
  const { mode } = useThemeMode();
  const themeConfig = useMemo(() => buildTheme(mode), [mode]);
  return (
    <ConfigProvider theme={themeConfig} componentSize="small" locale={zhCN}>
      <AntApp>{children}</AntApp>
    </ConfigProvider>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeModeProvider>
      <ThemedConfig>
        <BrowserRouter>
          <AuthProvider>
            <ApiFeedbackProvider>
              <App />
            </ApiFeedbackProvider>
          </AuthProvider>
        </BrowserRouter>
      </ThemedConfig>
    </ThemeModeProvider>
  </React.StrictMode>,
);
