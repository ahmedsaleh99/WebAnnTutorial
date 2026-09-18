import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { AuthGate } from "./AuthGate";
import { ErrorBoundary } from "./ErrorBoundary";
import "./styles.css";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("The #root element is missing from index.html.");
}

createRoot(rootElement).render(
  <StrictMode>
    <ErrorBoundary>
      <AuthGate />
    </ErrorBoundary>
  </StrictMode>,
);
