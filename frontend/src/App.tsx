import { useEffect, useState } from "react";

import type { AuthUser } from "./api";
import { navigationFor } from "./navigation";

interface AppProps {
  user: AuthUser;
  onLogout: () => void;
  loggingOut?: boolean;
  error?: string | null;
}

export function App({ user, onLogout, loggingOut = false, error = null }: AppProps) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    document.title = "WebAnn · Dashboard";
    setReady(true);
  }, []);

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#dashboard" aria-label="WebAnn home">
          WebAnn
        </a>
        <nav aria-label="Primary navigation">
          <ul>
            {navigationFor(user.role).map((item) => (
              <li key={item.href}>
                <a href={item.href}>{item.label}</a>
              </li>
            ))}
          </ul>
        </nav>
        <div className="account-actions" aria-label="Account controls">
          <button type="button" disabled title="Account menu arrives in a later lesson">
            User: {user.username}
          </button>
          <button type="button" onClick={onLogout} disabled={loggingOut}>
            {loggingOut ? "Logging out…" : "Log out"}
          </button>
        </div>
      </header>
      <main>
        {error && <p role="alert">{error}</p>}
        <p className="eyebrow">Annotation workspace</p>
        <h1>Dashboard</h1>
        <p>
          {ready
            ? "Your workspace is ready."
            : "Preparing your annotation workspace…"}
        </p>
        <section aria-labelledby="assigned-heading" className="summary-card">
          <h2 id="assigned-heading">Assigned work</h2>
          <p>Assignments will appear after the API is connected in Lesson 10.</p>
        </section>
      </main>
    </div>
  );
}
