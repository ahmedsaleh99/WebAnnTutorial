import { useEffect, useState } from "react";

import { navigationFor, type UserRole } from "./navigation";

interface AppProps {
  role?: UserRole;
}

export function App({ role = "annotator" }: AppProps) {
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
            {navigationFor(role).map((item) => (
              <li key={item.href}>
                <a href={item.href}>{item.label}</a>
              </li>
            ))}
          </ul>
        </nav>
        <div className="account-actions" aria-label="Account controls">
          <button type="button" disabled title="Account controls arrive with authentication">
            User: {role}
          </button>
          <button type="button" disabled title="Logout arrives with authentication">
            Log out
          </button>
        </div>
      </header>
      <main>
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
