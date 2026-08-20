import axios from "axios";

const timeout = Number(import.meta.env.VITE_API_TIMEOUT_MS ?? 30_000);

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",
  timeout: Number.isFinite(timeout) ? timeout : 30_000,
  withCredentials: true,
});
