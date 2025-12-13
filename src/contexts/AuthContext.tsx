import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import {
  AuthResponse,
  AuthUser,
  forgotPassword,
  login as loginApi,
  logout as logoutApi,
  me,
  requestOtp,
  resetPassword,
  signup as signupApi,
  verifyOtp,
} from "@/api/auth";
import { authTokenStore } from "@/api/client";

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (params: { email: string; password: string; first_name?: string; last_name?: string }) => Promise<void>;
  logout: () => Promise<void>;
  requestOtp: (email: string, purpose: "verify" | "reset") => Promise<void>;
  verifyOtp: (email: string, code: string, purpose: "verify" | "reset") => Promise<AuthResponse | { detail: string }>;
  forgotPassword: (email: string) => Promise<void>;
  resetPassword: (email: string, code: string, newPassword: string) => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(authTokenStore.get());
  const [loading, setLoading] = useState(true);

  const setAuth = (resp: AuthResponse) => {
    authTokenStore.set(resp.token);
    setToken(resp.token);
    setUser(resp.user);
  };

  useEffect(() => {
    const existing = authTokenStore.get();
    if (!existing) {
      setLoading(false);
      return;
    }
    me()
      .then((u) => setUser(u))
      .catch(() => {
        authTokenStore.set(null);
        setToken(null);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const resp = await loginApi({ email, password });
      setAuth(resp);
    } finally {
      setLoading(false);
    }
  };

  const signup = async (params: { email: string; password: string; first_name?: string; last_name?: string }) => {
    await signupApi(params);
  };

  const logout = async () => {
    await logoutApi();
    setUser(null);
    setToken(null);
  };

  const requestOtpHandler = async (email: string, purpose: "verify" | "reset") => {
    await requestOtp({ email, purpose });
  };

  const verifyOtpHandler = async (email: string, code: string, purpose: "verify" | "reset") => {
    const resp = await verifyOtp({ email, code, purpose });
    if ((resp as AuthResponse).token) {
      setAuth(resp as AuthResponse);
    }
    return resp;
  };

  const forgotPasswordHandler = async (email: string) => {
    await forgotPassword({ email });
  };

  const resetPasswordHandler = async (email: string, code: string, newPassword: string) => {
    await resetPassword({ email, code, new_password: newPassword });
  };

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      login,
      signup,
      logout,
      requestOtp: requestOtpHandler,
      verifyOtp: verifyOtpHandler,
      forgotPassword: forgotPasswordHandler,
      resetPassword: resetPasswordHandler,
      isAuthenticated: !!user && !!token,
    }),
    [user, token, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

