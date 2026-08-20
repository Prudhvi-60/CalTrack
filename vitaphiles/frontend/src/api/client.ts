import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import { getAccessToken, setAccessToken } from "@/api/token";

function resolveApiUrl(): string {
  return String(import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");
}

const baseURL = resolveApiUrl();
const timeout = Number(import.meta.env.VITE_API_TIMEOUT_MS ?? 30_000);

type RetryConfig = InternalAxiosRequestConfig & { _retry?: boolean };

export const api = axios.create({
  baseURL,
  timeout: Number.isFinite(timeout) ? timeout : 30_000,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

const refreshClient = axios.create({
  baseURL,
  timeout: 15_000,
  withCredentials: true,
});

let refreshInFlight: Promise<string | null> | null = null;

function isAuthUrl(url: string): boolean {
  return (
    url.includes("/auth/login") ||
    url.includes("/auth/register") ||
    url.includes("/auth/refresh") ||
    url.includes("/auth/logout")
  );
}

export async function refreshAccessToken(): Promise<string | null> {
  if (!refreshInFlight) {
    refreshInFlight = refreshClient
      .post("/api/v1/auth/refresh")
      .then((response) => {
        const token = response.data?.access_token as string | undefined;
        if (!token) {
          setAccessToken(null);
          return null;
        }
        setAccessToken(token);
        return token;
      })
      .catch(() => {
        setAccessToken(null);
        return null;
      })
      .finally(() => {
        refreshInFlight = null;
      });
  }
  return refreshInFlight;
}

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status = error.response?.status;
    const config = error.config as RetryConfig | undefined;
    const url = String(config?.url ?? "");
    if (status !== 401 || !config || config._retry || isAuthUrl(url)) {
      return Promise.reject(error);
    }
    config._retry = true;
    const token = await refreshAccessToken();
    if (!token) {
      window.dispatchEvent(new Event("vitaphiles:unauthorized"));
      return Promise.reject(error);
    }
    config.headers.Authorization = `Bearer ${token}`;
    return api(config);
  },
);
