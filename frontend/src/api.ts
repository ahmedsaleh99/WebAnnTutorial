export type UserRole = "annotator" | "manager" | "admin";

export interface AuthUser {
  id: number;
  username: string;
  role: UserRole;
  must_change_password: boolean;
}

export interface AuthSession {
  token: string;
  user: AuthUser;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number | null,
    readonly kind: "validation" | "unauthorized" | "forbidden" | "network" | "server",
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readUser(value: unknown): AuthUser {
  if (!isRecord(value)) throw new ApiError("Invalid user data from server.", null, "server");
  const { id, username, role, must_change_password } = value;
  if (
    typeof id !== "number" ||
    typeof username !== "string" ||
    (role !== "annotator" && role !== "manager" && role !== "admin") ||
    typeof must_change_password !== "boolean"
  ) {
    throw new ApiError("Invalid user data from server.", null, "server");
  }
  return { id, username, role, must_change_password };
}

function readSession(value: unknown): AuthSession {
  if (!isRecord(value) || typeof value.token !== "string" || !value.token) {
    throw new ApiError("Invalid sign-in response from server.", null, "server");
  }
  return { token: value.token, user: readUser(value.user) };
}

function errorMessage(value: unknown): string | null {
  if (!isRecord(value)) return null;
  if (typeof value.detail === "string") return value.detail;
  for (const [field, messages] of Object.entries(value)) {
    if (Array.isArray(messages) && typeof messages[0] === "string") {
      return `${field}: ${messages[0]}`;
    }
  }
  return null;
}

export async function request(path: string, method: "GET" | "POST" | "PATCH" | "DELETE", body?: object, token?: string): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(path, {
      method,
      headers: {
        Accept: "application/json",
        ...(body ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Token ${token}` } : {}),
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
      credentials: "same-origin",
      cache: "no-store",
    });
  } catch {
    throw new ApiError("Cannot reach the server. Check your connection and try again.", null, "network");
  }

  const raw = await response.text();
  let data: unknown = null;
  try {
    data = raw ? JSON.parse(raw) : null;
  } catch {
    throw new ApiError("The server returned an invalid response.", response.status, "server");
  }
  if (!response.ok) {
    const kind = response.status === 401 ? "unauthorized" :
      response.status === 403 ? "forbidden" :
      response.status === 400 ? "validation" : "server";
    throw new ApiError(errorMessage(data) ?? `Request failed (${response.status}).`, response.status, kind);
  }
  return data;
}

export async function signIn(username: string, password: string): Promise<AuthSession> {
  return readSession(await request("/api/auth/login/", "POST", { username, password }));
}

export async function currentUser(token: string): Promise<AuthUser> {
  return readUser(await request("/api/auth/me/", "GET", undefined, token));
}

export async function changePassword(
  token: string,
  currentPassword: string,
  newPassword: string,
  confirmation: string,
): Promise<AuthSession> {
  return readSession(await request("/api/auth/password-change/", "POST", {
    current_password: currentPassword,
    new_password: newPassword,
    new_password_confirmation: confirmation,
  }, token));
}

export async function signOut(token: string): Promise<void> {
  await request("/api/auth/logout/", "POST", undefined, token);
}
