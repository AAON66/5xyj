import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App";
import { ApiFeedbackProvider } from "./components";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ApiFeedbackProvider>
        <App />
      </ApiFeedbackProvider>
    </BrowserRouter>
  </React.StrictMode>,
);