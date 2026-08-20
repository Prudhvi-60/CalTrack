import { isAxiosError } from "axios";
import { api } from "./client";
import { setAccessToken } from "./token";
import type { TokenResponse, User } from "@/types/auth";

export type RegisterPayload = {
  email: string;
  username: string;
  display_name: string;
  password: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

function storeAccess(result: TokenResponse): TokenResponse {
  setAccessToken(result.access_token);
  return result;
}

export async function registerUser(payload: RegisterPayload): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/api/v1/auth/register", payload);
  return storeAccess(data);
}

export async function loginUser(payload: LoginPayload): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/api/v1/auth/login", payload);
  return storeAccess(data);
}

export async function getCurrentUser(): Promise<User> {
  const { data } = await api.get<User>("/api/v1/auth/me");
  return data;
}

export async function logoutUser(): Promise<void> {
  try {
    await api.post("/api/v1/auth/logout");
  } finally {
    setAccessToken(null);
  }
}

export async function updateProfile(payload: { display_name?: string; bio?: string | null }): Promise<User> {
  const { data } = await api.patch<User>("/api/v1/auth/me", payload);
  return data;
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  await api.post("/api/v1/auth/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
}

export function getApiErrorMessage(error: unknown, fallback = "Something went wrong"): string {
  if (isAxiosError(error)) {
    if (error.code === "ECONNABORTED") {
      return "The request timed out. Please try again.";
    }
    if (!error.response) {
      return "Could not reach the server. Check your connection and try again.";
    }
    const status = error.response.status;
    const message = error.response.data?.error?.message;
    if (status === 401) {
      return typeof message === "string" && message.length > 0 ? message : "Please sign in again.";
    }
    if (status === 409) {
      return typeof message === "string" && message.length > 0 ? message : "That account already exists.";
    }
    if (status === 422) {
      return typeof message === "string" && message.length > 0 ? message : "Please check the form and try again.";
    }
    if (status === 429) {
      return "Too many requests. Please wait a moment and try again.";
    }
    if (status >= 500) {
      return "Something went wrong on the server. Please try again.";
    }
    if (typeof message === "string" && message.length > 0) {
      return message;
    }
  }
  return fallback;
}
