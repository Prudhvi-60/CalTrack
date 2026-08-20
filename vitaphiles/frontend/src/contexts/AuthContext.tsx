import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  changePassword,
  getCurrentUser,
  loginUser,
  logoutUser,
  registerUser,
  updateProfile,
  type LoginPayload,
  type RegisterPayload,
} from "@/api/auth";
import { refreshAccessToken } from "@/api/client";
import { getAccessToken, setAccessToken } from "@/api/token";
import { queryClient } from "@/lib/queryClient";
import type { User } from "@/types/auth";

type AuthContextValue = {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  saveProfile: (payload: { display_name?: string; bio?: string }) => Promise<void>;
  savePassword: (currentPassword: string, newPassword: string) => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);
const AUTH_CHANNEL = "vitaphiles-auth";

function notifyTabs(type: "login" | "logout") {
  if (typeof BroadcastChannel === "undefined") {
    return;
  }
  const channel = new BroadcastChannel(AUTH_CHANNEL);
  channel.postMessage(type);
  channel.close();
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const clearSession = useCallback(() => {
    setAccessToken(null);
    setUser(null);
    queryClient.clear();
  }, []);

  useEffect(() => {
    function onUnauthorized() {
      clearSession();
    }
    window.addEventListener("vitaphiles:unauthorized", onUnauthorized);
    return () => window.removeEventListener("vitaphiles:unauthorized", onUnauthorized);
  }, [clearSession]);

  useEffect(() => {
    if (typeof BroadcastChannel === "undefined") {
      return;
    }
    const channel = new BroadcastChannel(AUTH_CHANNEL);
    channel.onmessage = (event) => {
      if (event.data === "logout") {
        clearSession();
      }
    };
    return () => channel.close();
  }, [clearSession]);

  useEffect(() => {
    let cancelled = false;
    async function restore() {
      try {
        const token = (await refreshAccessToken()) ?? getAccessToken();
        if (!token) {
          return;
        }
        const profile = await getCurrentUser();
        if (!cancelled) {
          setUser(profile);
        }
      } catch {
        if (!cancelled) {
          clearSession();
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }
    void restore();
    return () => {
      cancelled = true;
    };
  }, [clearSession]);

  const login = useCallback(async (payload: LoginPayload) => {
    const result = await loginUser(payload);
    setUser(result.user);
    notifyTabs("login");
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    const result = await registerUser(payload);
    setUser(result.user);
    notifyTabs("login");
  }, []);

  const logout = useCallback(async () => {
    try {
      await logoutUser();
    } catch {
      setAccessToken(null);
    }
    setUser(null);
    queryClient.clear();
    notifyTabs("logout");
  }, []);

  const saveProfile = useCallback(async (payload: { display_name?: string; bio?: string }) => {
    const updated = await updateProfile(payload);
    setUser(updated);
  }, []);

  const savePassword = useCallback(async (currentPassword: string, newPassword: string) => {
    await changePassword(currentPassword, newPassword);
    setAccessToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      isLoading,
      isAuthenticated: user !== null,
      login,
      register,
      logout,
      saveProfile,
      savePassword,
    }),
    [user, isLoading, login, register, logout, saveProfile, savePassword],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
