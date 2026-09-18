import { useState, type SubmitEvent } from "react";

import { App } from "./App";
import { ApiError, changePassword, signIn, signOut, type AuthSession } from "./api";

function messageFor(error: unknown): string {
  return error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
}

function field(form: HTMLFormElement, name: string): string {
  return String(new FormData(form).get(name) ?? "");
}

export function AuthGate() {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [pending, setPending] = useState<"sign-in" | "password" | "logout" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSignIn(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending("sign-in");
    setError(null);
    try {
      const nextSession = await signIn(
        field(event.currentTarget, "username"),
        field(event.currentTarget, "password"),
      );
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
      const nextSession = await changePassword(
        session.token,
        field(event.currentTarget, "current_password"),
        field(event.currentTarget, "new_password"),
        field(event.currentTarget, "new_password_confirmation"),
      );
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
      <main className="auth-page">
        <h1>Sign in to WebAnn</h1>
        <p>Use your WebAnn username and password.</p>
        <form key="sign-in" onSubmit={handleSignIn}>
          <label htmlFor="username">Username</label>
          <input id="username" name="username" autoComplete="username" required />
          <label htmlFor="password">Password</label>
          <input id="password" name="password" type="password" autoComplete="current-password" required />
          {error && <p role="alert">{error}</p>}
          <button type="submit" disabled={pending !== null}>
            {pending === "sign-in" ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </main>
    );
  }

  if (session.user.must_change_password) {
    return (
      <main className="auth-page">
        <h1>Change your password</h1>
        <p>You must change your password before entering the workspace.</p>
        <form key="change-password" onSubmit={handlePasswordChange}>
          <label htmlFor="current-password">Current password</label>
          <input id="current-password" name="current_password" type="password" autoComplete="current-password" required />
          <label htmlFor="new-password">New password</label>
          <input id="new-password" name="new_password" type="password" autoComplete="new-password" required />
          <label htmlFor="confirm-password">Confirm new password</label>
          <input id="confirm-password" name="new_password_confirmation" type="password" autoComplete="new-password" required />
          {error && <p role="alert">{error}</p>}
          <button type="submit" disabled={pending !== null}>
            {pending === "password" ? "Changing password…" : "Change password"}
          </button>
        </form>
      </main>
    );
  }

  return <App user={session.user} onLogout={handleLogout} loggingOut={pending === "logout"} error={error} />;
}
