import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { API_BASE_URL, STORAGE_KEYS } from "@/constants/config";
import { secureStorage } from "@/services/storage/secureStorage";

/**
 * Shared Axios instance for all API calls.
 * Ref: docs/05_BACKEND_API_SPECIFICATION.txt, Section 1 (General API
 * Conventions) - versioned base path, JWT bearer auth, consistent error
 * shape.
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  const token = await secureStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    // 401 handling / refresh-token exchange (POST /auth/refresh) would be
    // wired up here in a full implementation. Kept minimal for Phase 1.
    return Promise.reject(error);
  }
);

export interface ApiErrorShape {
  error: {
    code: string;
    message: string;
    fields?: Record<string, string>;
  };
}
