import axios, { AxiosError, AxiosRequestConfig, InternalAxiosRequestConfig } from "axios";
import { API_BASE_URL, STORAGE_KEYS } from "@/constants/config";
import { secureStorage } from "@/services/storage/secureStorage";

/**
 * Shared Axios instance.
 * Ref: docs/05_BACKEND_API_SPECIFICATION.txt §1 (General API Conventions)
 *
 * The backend always replies with an envelope:
 *   success -> { success: true,  message, data }
 *   failure -> { success: false, message, errors: [], code?, data? }
 *
 * Callers should use apiGet/apiPost/apiPut below, which return the inner
 * `data` payload directly, so no feature code has to know the envelope exists.
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

/** Envelope shape returned by every backend endpoint. */
interface ApiEnvelope<T> {
  success: boolean;
  message: string;
  data?: T;
  errors?: string[];
  code?: string;
}

/**
 * Normalised error thrown by every API helper, so screens can show the
 * backend's own message ("Invalid email or password.") instead of a
 * generic one, and can switch on `code` for specific handling (e.g.
 * "EMAIL_NOT_VERIFIED", "ACCOUNT_LOCKED").
 */
export class ApiError extends Error {
  status: number;
  errors: string[];
  code?: string;
  data?: unknown;

  constructor(message: string, status: number, errors: string[] = [], code?: string, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.errors = errors;
    this.code = code;
    this.data = data;
  }
}

// ---------------------------------------------------------------------------
// Request: attach the access token
// ---------------------------------------------------------------------------

apiClient.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  if (config.headers?.["X-Skip-Auth"]) {
    delete config.headers["X-Skip-Auth"];
    return config;
  }

  const token = await secureStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---------------------------------------------------------------------------
// Response: 401 -> refresh -> retry (single-flight)
// ---------------------------------------------------------------------------

let refreshPromise: Promise<string | null> | null = null;

/**
 * Exchanges the stored refresh token for a new pair.
 *
 * The backend ROTATES on refresh: the presented refresh token is revoked
 * and a brand new refresh token is issued. Both tokens must be stored, or
 * the next refresh will fail with 401.
 */
async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = await secureStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  if (!refreshToken) return null;

  try {
    const response = await axios.post<ApiEnvelope<{ access_token: string; refresh_token: string }>>(
      `${API_BASE_URL}/auth/refresh`,
      {},
      { headers: { Authorization: `Bearer ${refreshToken}` }, timeout: 15000 }
    );

    const tokens = response.data?.data;
    if (!tokens?.access_token) return null;

    await secureStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.access_token);
    if (tokens.refresh_token) {
      await secureStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refresh_token);
    }
    return tokens.access_token;
  } catch {
    await secureStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    await secureStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    return null;
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiEnvelope<unknown>>) => {
    const original = error.config as (AxiosRequestConfig & { _retried?: boolean }) | undefined;
    const status = error.response?.status;

    const isAuthEndpoint = typeof original?.url === "string" && original.url.startsWith("/auth/");

    if (status === 401 && original && !original._retried && !isAuthEndpoint) {
      original._retried = true;

      refreshPromise = refreshPromise ?? refreshAccessToken();
      const newToken = await refreshPromise;
      refreshPromise = null;

      if (newToken) {
        original.headers = { ...(original.headers ?? {}), Authorization: `Bearer ${newToken}` };
        return apiClient(original);
      }
    }

    return Promise.reject(error);
  }
);

// ---------------------------------------------------------------------------
// Typed helpers — return the inner `data` payload, throw ApiError on failure
// ---------------------------------------------------------------------------

function toApiError(error: unknown): ApiError {
  const axiosError = error as AxiosError<ApiEnvelope<unknown>>;

  if (axiosError?.response) {
    const body = axiosError.response.data;
    return new ApiError(
      body?.message || "Something went wrong. Please try again.",
      axiosError.response.status,
      body?.errors ?? [],
      body?.code,
      body?.data
    );
  }

  if (axiosError?.code === "ECONNABORTED") {
    return new ApiError("The server took too long to respond. Please try again.", 0);
  }

  return new ApiError(
    "Can't reach the server. Check your connection and that the backend is running.",
    0
  );
}

export async function apiPost<T>(url: string, body?: unknown, config?: AxiosRequestConfig): Promise<T> {
  try {
    const response = await apiClient.post<ApiEnvelope<T>>(url, body ?? {}, config);
    return (response.data?.data ?? {}) as T;
  } catch (error) {
    throw toApiError(error);
  }
}

export async function apiGet<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  try {
    const response = await apiClient.get<ApiEnvelope<T>>(url, config);
    return (response.data?.data ?? {}) as T;
  } catch (error) {
    throw toApiError(error);
  }
}

export async function apiPut<T>(url: string, body?: unknown, config?: AxiosRequestConfig): Promise<T> {
  try {
    const response = await apiClient.put<ApiEnvelope<T>>(url, body ?? {}, config);
    return (response.data?.data ?? {}) as T;
  } catch (error) {
    throw toApiError(error);
  }
}

export async function apiDelete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  try {
    const response = await apiClient.delete<ApiEnvelope<T>>(url, config);
    return (response.data?.data ?? {}) as T;
  } catch (error) {
    throw toApiError(error);
  }
}



/**
 * Safe error-message extraction for UI display. Falls back to a generic
 * message for anything that ISN'T an ApiError (e.g. a plain crash
 * elsewhere in the app), so a screen always shows SOMETHING instead of
 * silently doing nothing.
 */
export function getErrorMessage(
  error: unknown,
  fallback = "Something went wrong. Please try again."
): string {
  if (error instanceof ApiError) return error.message;
  return fallback;
}