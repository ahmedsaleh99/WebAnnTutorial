import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthGate } from "./AuthGate";

const user = { id: 1, username: "amina", role: "annotator", must_change_password: false };
const response = (status: number, data: unknown) => ({
  ok: status >= 200 && status < 300,
  status,
  text: async () => data === null ? "" : JSON.stringify(data),
});

async function enterCredentials() {
  const actor = userEvent.setup();
  await actor.type(screen.getByRole("textbox", { name: "Username" }), "amina");
  await actor.type(screen.getByLabelText("Password"), "Password9!");
  await actor.click(screen.getByRole("button", { name: "Sign in" }));
  return actor;
}

afterEach(() => vi.unstubAllGlobals());

describe("AuthGate", () => {
  it("shows a loading state and prevents a second sign-in request", async () => {
    let finishRequest: ((value: ReturnType<typeof response>) => void) | undefined;
    const pendingResponse = new Promise<ReturnType<typeof response>>((resolve) => {
      finishRequest = resolve;
    });
    const fetchMock = vi.fn().mockReturnValue(pendingResponse);
    vi.stubGlobal("fetch", fetchMock);
    render(<AuthGate />);

    await enterCredentials();

    expect(screen.getByRole("button", { name: "Signing in…" })).toBeDisabled();
    expect(fetchMock).toHaveBeenCalledOnce();
    finishRequest?.(response(200, { token: "secret", user }));
    expect(await screen.findByRole("heading", { name: "My jobs" })).toBeInTheDocument();
  });

  it("starts at sign in and shows Jobs after a valid login", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response(200, { token: "secret", user }));
    vi.stubGlobal("fetch", fetchMock);
    render(<AuthGate />);

    await enterCredentials();

    expect(await screen.findByRole("heading", { name: "My jobs" })).toBeInTheDocument();
    expect(screen.getByText("amina")).toBeInTheDocument();
  });

  it("shows validation errors and keeps the sign-in form available", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(400, { detail: "Invalid username or password." })));
    render(<AuthGate />);

    await enterCredentials();

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid username or password.");
    expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled();
  });

  it("shows a useful network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<AuthGate />);

    await enterCredentials();

    expect(await screen.findByRole("alert")).toHaveTextContent("Cannot reach the server");
  });

  it("requires password change and replaces the revoked token", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response(200, { token: "old-token", user: { ...user, must_change_password: true } }))
      .mockResolvedValueOnce(response(400, { detail: "The new passwords do not match." }))
      .mockResolvedValueOnce(response(200, { token: "new-token", user }));
    vi.stubGlobal("fetch", fetchMock);
    render(<AuthGate />);
    const actor = await enterCredentials();

    expect(await screen.findByRole("heading", { name: "Change password" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Secure your account." })).toBeInTheDocument();
    expect(screen.queryByLabelText("Username")).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "My jobs" })).not.toBeInTheDocument();
    expect(screen.getByLabelText("Current password")).toHaveValue("");
    expect(screen.getByLabelText("New password")).toHaveValue("");
    expect(screen.getByLabelText("Confirm new password")).toHaveValue("");
    await actor.type(screen.getByLabelText("Current password"), "Password9!");
    await actor.type(screen.getByLabelText("New password"), "NewPassword9!");
    await actor.type(screen.getByLabelText("Confirm new password"), "different");
    await actor.click(screen.getByRole("button", { name: "Change password and continue" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("do not match");

    await actor.clear(screen.getByLabelText("Confirm new password"));
    await actor.type(screen.getByLabelText("Confirm new password"), "NewPassword9!");
    await actor.click(screen.getByRole("button", { name: "Change password and continue" }));

    expect(await screen.findByRole("heading", { name: "My jobs" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/auth/password-change/", expect.objectContaining({
      headers: expect.objectContaining({ Authorization: "Token old-token" }),
    }));
  });

  it("returns to sign in when the password-change token is unauthorized", async () => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(response(200, { token: "expired", user: { ...user, must_change_password: true } }))
      .mockResolvedValueOnce(response(401, { detail: "Invalid token." })));
    render(<AuthGate />);
    const actor = await enterCredentials();
    await screen.findByRole("heading", { name: "Change password" });

    await actor.type(screen.getByLabelText("Current password"), "Password9!");
    await actor.type(screen.getByLabelText("New password"), "NewPassword9!");
    await actor.type(screen.getByLabelText("Confirm new password"), "NewPassword9!");
    await actor.click(screen.getByRole("button", { name: "Change password and continue" }));

    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Invalid token.");
  });

  it("revokes the token and returns to sign in on logout", async () => {
    const fetchMock = vi.fn((path: string) => Promise.resolve(
      path === "/api/auth/login/" ? response(200, { token: "secret", user })
        : path === "/api/auth/logout/" ? response(204, null)
          : response(200, { count: 0, next: null, previous: null, results: [] }),
    ));
    vi.stubGlobal("fetch", fetchMock);
    render(<AuthGate />);
    const actor = await enterCredentials();
    await screen.findByRole("heading", { name: "My jobs" });

    await actor.click(screen.getByRole("button", { name: "Sign out" }));

    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith("/api/auth/logout/", expect.objectContaining({
      headers: expect.objectContaining({ Authorization: "Token secret" }),
    }));
  });
});
