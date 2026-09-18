import { afterEach, describe, expect, it, vi } from "vitest";

import { changePassword, currentUser, signIn, signOut } from "./api";

const user = { id: 1, username: "amina", role: "annotator", must_change_password: true };
const response = (status: number, data: unknown) => ({
  ok: status >= 200 && status < 300,
  status,
  text: async () => data === null ? "" : JSON.stringify(data),
});

afterEach(() => vi.unstubAllGlobals());

describe("auth API client", () => {
  it("sends credentials to the same-origin login endpoint and validates the response", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response(200, { token: "secret", user: user }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(signIn("amina", "password")).resolves.toEqual({ token: "secret", user: user });
    expect(fetchMock).toHaveBeenCalledWith("/api/auth/login/", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ username: "amina", password: "password" }),
      credentials: "same-origin",
      headers: expect.objectContaining({
        "Content-Type": "application/json",
        Accept: "application/json",
      }),
    }));
  });

  it("rejects malformed success data rather than trusting a TypeScript type", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(200, { token: "secret", user: { role: "unknown" } })));

    await expect(signIn("amina", "password")).rejects.toMatchObject({ kind: "server" });
  });

  it("reports server validation errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(400, { detail: "Invalid username or password." })));

    await expect(signIn("amina", "wrong")).rejects.toMatchObject({
      kind: "validation", status: 400, message: "Invalid username or password.",
    });
  });

  it("reports network failures without exposing a token", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    await expect(signIn("amina", "password")).rejects.toMatchObject({ kind: "network", status: null });
  });

  it("rejects an HTML success response instead of treating it as JSON", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true, status: 200, text: async () => "<html>Unexpected page</html>",
    }));

    await expect(signIn("amina", "password")).rejects.toMatchObject({ kind: "server" });
  });

  it("distinguishes forbidden access from invalid credentials", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(403, { detail: "Not allowed." })));

    await expect(currentUser("secret")).rejects.toMatchObject({
      kind: "forbidden", status: 403, message: "Not allowed.",
    });
  });

  it("sends the token only in the authorization header", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response(200, user));
    vi.stubGlobal("fetch", fetchMock);

    await expect(currentUser("secret")).resolves.toEqual(user);
    expect(fetchMock).toHaveBeenCalledWith("/api/auth/me/", expect.objectContaining({
      headers: expect.objectContaining({ Authorization: "Token secret" }),
    }));
  });

  it("uses the rotated token from a successful password change", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response(200, {
      token: "new-secret", user: { ...user, must_change_password: false },
    }));
    vi.stubGlobal("fetch", fetchMock);

    const session = await changePassword("old-secret", "old", "new", "new");

    expect(session.token).toBe("new-secret");
    expect(fetchMock).toHaveBeenCalledWith("/api/auth/password-change/", expect.objectContaining({
      headers: expect.objectContaining({ Authorization: "Token old-secret" }),
    }));
  });

  it("treats expired tokens as unauthorized and accepts an empty logout response", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response(401, { detail: "Invalid token." }))
      .mockResolvedValueOnce(response(204, null));
    vi.stubGlobal("fetch", fetchMock);

    await expect(currentUser("expired")).rejects.toMatchObject({ kind: "unauthorized", status: 401 });
    await expect(signOut("secret")).resolves.toBeUndefined();
  });
});
