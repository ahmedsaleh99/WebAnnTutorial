import { useEffect, useState } from "react";

import type { AuthUser } from "./api";
import { navigationFor } from "./navigation";
import { TemplatesPage } from "./TemplatesPage";

interface AppProps {
  user: AuthUser;
  onLogout: () => void;
  loggingOut?: boolean;
  error?: string | null;
  token?: string;
  onUnauthorized?: () => void;
}

const ignoreUnauthorized = () => undefined;

export function App({ user, onLogout, loggingOut = false, error = null, token = "", onUnauthorized = ignoreUnauthorized }: AppProps) {
  const [section, setSection] = useState(window.location.hash);

  useEffect(() => {
    const updateSection = () => setSection(window.location.hash);
    window.addEventListener("hashchange", updateSection);
    return () => window.removeEventListener("hashchange", updateSection);
  }, []);

  useEffect(() => {
    const title = navigationFor(user.role).find((item) => item.href === section)?.label ?? "Jobs";
    document.title = `${title} · Annotation Platform`;
  }, [section, user.role]);

  return (
    <div className="dashboard">
      <header className="topbar">
        <div className="brand-mark small" aria-hidden="true">SE</div>
        <strong>Annotation Platform</strong>
        <nav aria-label="Primary navigation">
          {navigationFor(user.role).map((item) => (
            <button
              key={item.href}
              type="button"
              className={item.href === (section || "#jobs") ? "active" : ""}
              aria-current={item.href === (section || "#jobs") ? "page" : undefined}
              onClick={() => { window.location.hash = item.href; }}
            >
              {item.href === "#jobs" && user.role === "annotator" ? "My Jobs" : item.label}
            </button>
          ))}
        </nav>
        <div className="account" aria-label="Account controls">
          <span>{user.username}<small>{user.role === "admin" ? "Admin" : user.role === "manager" ? "Manager" : "Annotator"}</small></span>
          <button type="button" onClick={onLogout} disabled={loggingOut}>
            {loggingOut ? "Signing out…" : "Sign out"}
          </button>
        </div>
      </header>
      <main className="content">
        {error && <p role="alert">{error}</p>}
        {section === "#templates" && user.role === "admin" ? <TemplatesPage token={token} onUnauthorized={onUnauthorized} />
          : <section aria-labelledby="workspace-heading" className="workspace-placeholder">
            <div className="page-heading"><div><small>WORKSPACE</small><h1 id="workspace-heading">
              {section && navigationFor(user.role).some((item) => item.href === section) && section !== "#jobs"
                ? navigationFor(user.role).find((item) => item.href === section)?.label
                : user.role === "annotator" ? "My jobs" : "Annotation jobs"}
            </h1></div></div>
            <p>This workflow is covered in a later lesson.</p>
          </section>}
      </main>
    </div>
  );
}
