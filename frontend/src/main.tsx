import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ConfigProvider, App as AntApp } from "antd";
import zhCN from "antd/locale/zh_CN";

import App from "./App";
import { ApiFeedbackProvider, AuthProvider } from "./components";
import { theme } from "./theme";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider theme={theme} componentSize="small" locale={zhCN}>
      <AntApp>
        <BrowserRouter>
          <AuthProvider>
            <ApiFeedbackProvider>
              <App />
            </ApiFeedbackProvider>
          </AuthProvider>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  </React.StrictMode>,
);
