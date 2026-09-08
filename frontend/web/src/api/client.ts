/**
 * The web's HTTP transport. LAYER 1 -- it may import from lib/ and
 * config/ and nothing else. No React, no components, no domain logic.
 *
 * Ref: docs/05_BACKEND_API_SPECIFICATION.txt section 1.
 *
 * The backend always replies with an envelope:
 *   success -> { success: true,  message, data }
 *   failure -> { success: false, message, errors: [], code?, data? }
 *
 * Callers use the helpers below, which return the inner `data` directly,
 * so no domain or surface code has to know the envelope exists. Same
 * contract the mobile client honours -- see
 * frontend/mobile/src/services/api/apiClient.ts.
 *
 * ─────────────────────────────────────────────────────────────────────
 * WHY `credentials: "include"` AND NO Authorization HEADER
 *
 * The mobile app holds a JWT and sends `Authorization: Bearer`. A
 * browser must NOT do that. Anything reachable from JavaScript --
 * localStorage, sessionStorage, a module variable -- is readable by any
 * XSS that lands on the page, and a stolen supplier token is a stolen
 * catalogue.
 *
 * So the portal authenticates with an httpOnly, Secure, SameSite cookie
 * that JavaScript cannot read at all. That is why this file sends
 * credentials and never a token: there is no token here to send.
 *
 * The cost is CSRF, which bearer tokens do not have. `unsafeRequest`
 * below attaches the CSRF token for every mutating verb.
 *
 * NEITHER HALF EXISTS ON THE BACKEND YET (V2_00 section 2.10). This file
 * is written against the shape it will have, and the auth endpoints stay
 * unwired until it does.
 * ─────────────────────────────────────────────────────────────────────
 */
import { API_BASE_URL } from "@/config/env";

interface ApiEnvelope<T> {
  success: boolean;
  message: string;
  data?: T;
  errors?: string[];
  code?: string;
}

/**
 * Normalised error carrying the backend's own message and stable `code`
 * ("EMAIL_NOT_VERIFIED", "ACCOUNT_LOCKED"), so a surface can show what
 * the server actually said and branch on the code rather than on
 * matching strings.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly errors: string[];
  readonly code?: string;

  constructor(
    message: string,
    status: number,
    errors: string[] = [],
    code?: string,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.errors = errors;
    this.code = code;
  }
}

/** Verbs that change state, and therefore need a CSRF token. */
const UNSAFE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

/**
 * The CSRF token is set by the backend as a READABLE cookie alongside
 * the httpOnly session cookie, and echoed back in a header. An attacker
 * on another origin can cause the session cookie to be sent, but cannot
 * read this one to build the matching header -- which is the whole
 * mechanism.
 */
function readCsrfToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
}

async function request<T>(
  path: string,
  init: RequestInit & { method?: string } = {},
): Promise<T> {
  const method = (init.method ?? "GET").toUpperCase();
  const headers = new Headers(init.headers);

  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }

  if (UNSAFE_METHODS.has(method)) {
    const csrf = readCsrfToken();
    if (csrf) headers.set("X-CSRF-Token", csrf);
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      method,
      headers,
      // Send and accept the session cookie. Without this the portal is
      // permanently signed out no matter what the backend issues.
      credentials: "include",
    });
  } catch {
    // A network failure is not an HTTP status. Give it one the callers
    // can branch on rather than leaking a raw TypeError upward.
    throw new ApiError("Cannot reach TruConnect. Check your connection.", 0);
  }

  // 204 and friends carry no body; parsing them would throw.
  const text = await response.text();
  let envelope: ApiEnvelope<T> | null = null;
  if (text) {
    try {
      envelope = JSON.parse(text) as ApiEnvelope<T>;
    } catch {
      throw new ApiError(
        "TruConnect returned an unexpected response.",
        response.status,
      );
    }
  }

  if (!response.ok || (envelope && envelope.success === false)) {
    throw new ApiError(
      envelope?.message ?? "Something went wrong.",
      response.status,
      envelope?.errors ?? [],
      envelope?.code,
    );
  }

  return (envelope?.data ?? undefined) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body ?? {}) }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body ?? {}) }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body ?? {}) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
