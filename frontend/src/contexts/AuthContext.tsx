import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { loginUser, logoutUser, registerUser, getCurrentUser, updateProfile, type LoginPayload, type RegisterPayload } from "@/api/auth";
import { refreshAccessToken } from "@/api/client";
import { getAccessToken, setAccessToken } from "@/api/token";
import { clearUserQueries } from "@/queryClient";
import type { User } from "@/types/auth";

type AuthContextValue = {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  setUserName: (name: string) => Promise<void>;
  updateUser: (payload: { name?: string; allow_training_data_collection?: boolean }) => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);
const AUTH_CHANNEL = "caltrack-auth";

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
    clearUserQueries();
  }, []);

  useEffect(() => {
    function onUnauthorized() {
      clearSession();
    }
    window.addEventListener("caltrack:unauthorized", onUnauthorized);
    return () => window.removeEventListener("caltrack:unauthorized", onUnauthorized);
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
    clearUserQueries();
    notifyTabs("logout");
  }, []);

  const updateUser = useCallback(
    async (payload: { name?: string; allow_training_data_collection?: boolean }) => {
      const updated = await updateProfile(payload);
      setUser(updated);
    },
    [],
  );

  const setUserName = useCallback(async (name: string) => {
    await updateUser({ name });
  }, [updateUser]);

  const value = useMemo(
    () => ({
      user,
      isLoading,
      isAuthenticated: user !== null,
      login,
      register,
      logout,
      setUserName,
      updateUser,
    }),
    [user, isLoading, login, register, logout, setUserName, updateUser],
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
