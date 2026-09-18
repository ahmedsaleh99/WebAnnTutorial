import { useCallback, useState, type SubmitEvent } from "react";

import { App } from "./App";
import { ApiError, changePassword, signIn, signOut, type AuthSession } from "./api";

function messageFor(error: unknown): string {
  return error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
}

function LoginBrand({ title, description }: { title: string; description: string }) {
  return (
    <section className="login-brand">
      <p className="welcome-institution"><strong>CVIP LAB</strong><span>UNIVERSITY OF LOUISVILLE</span></p>
      <h1>{title}</h1>
      <p>{description}</p>
    </section>
  );
}

export function AuthGate() {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [pending, setPending] = useState<"sign-in" | "password" | "logout" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const onUnauthorized = useCallback(() => setSession(null), []);

  async function handleSignIn(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending("sign-in");
    setError(null);
    try {
      const nextSession = await signIn(username, password);
      setPassword("");
      setSession(nextSession);
    } catch (failure) {
      setError(messageFor(failure));
    } finally {
      setPending(null);
    }
  }

  async function handlePasswordChange(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) return;
    setPending("password");
    setError(null);
    try {
      const nextSession = await changePassword(session.token, currentPassword, newPassword, confirmation);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmation("");
      setSession(nextSession);
    } catch (failure) {
      if (failure instanceof ApiError && failure.kind === "unauthorized") setSession(null);
      setError(messageFor(failure));
    } finally {
      setPending(null);
    }
  }

  async function handleLogout() {
    if (!session) return;
    setPending("logout");
    setError(null);
    try {
      await signOut(session.token);
      setSession(null);
    } catch (failure) {
      if (failure instanceof ApiError && failure.kind === "unauthorized") setSession(null);
      setError(messageFor(failure));
    } finally {
      setPending(null);
    }
  }

  if (!session) {
    return (
      <main className="login-page">
        <LoginBrand title="Understand Student Engagement through Video" description="A specialized workspace for synchronizing classroom recordings and creating precise, subject-level engagement annotations across multiple camera views." />
        <section className="login-panel">
          <form key="sign-in" onSubmit={handleSignIn}>
            <header><small>WELCOME BACK</small><h2>Sign in</h2><p>Use your annotation platform account.</p></header>
            {error && <p role="alert">{error}</p>}
            <label htmlFor="username">Username<input id="username" name="username" autoFocus autoComplete="username" value={username} onChange={(event) => setUsername(event.currentTarget.value)} required /></label>
            <label htmlFor="password">Password<input id="password" name="password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.currentTarget.value)} required /></label>
            <button type="submit" disabled={pending !== null || !username || !password}>
              {pending === "sign-in" ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  if (session.user.must_change_password) {
    return (
      <main className="login-page">
        <LoginBrand title="Secure your account." description="Your administrator may have assigned a temporary password. Choose a private password before continuing to the annotation platform." />
        <section className="login-panel">
          <form key="change-password" onSubmit={handlePasswordChange}>
            <header><small>FIRST SIGN IN</small><h2>Change password</h2><p>Choose a new password with at least 8 characters.</p></header>
            {error && <p role="alert">{error}</p>}
            <label htmlFor="current-password">Current password<input id="current-password" name="current_password" autoFocus type="password" autoComplete="current-password" value={currentPassword} onChange={(event) => setCurrentPassword(event.currentTarget.value)} required /></label>
            <label htmlFor="new-password">New password<input id="new-password" name="new_password" type="password" autoComplete="new-password" minLength={8} value={newPassword} onChange={(event) => setNewPassword(event.currentTarget.value)} required /></label>
            <label htmlFor="confirm-password">Confirm new password<input id="confirm-password" name="new_password_confirmation" type="password" autoComplete="new-password" minLength={8} value={confirmation} onChange={(event) => setConfirmation(event.currentTarget.value)} required /></label>
            <button type="submit" disabled={pending !== null || !currentPassword || newPassword.length < 8 || !confirmation}>
              {pending === "password" ? "Changing password…" : "Change password and continue"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return <App user={session.user} token={session.token} onUnauthorized={onUnauthorized} onLogout={handleLogout} loggingOut={pending === "logout"} error={error} />;
}
