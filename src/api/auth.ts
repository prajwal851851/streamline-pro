import { apiGet, apiPost, authTokenStore } from "./client";

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
}

export interface AuthResponse {
  token: string;
  user: AuthUser;
}

export async function signup(payload: {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}) {
  return apiPost<{ detail: string }>("/auth/signup/", payload);
}

export async function login(payload: { email: string; password: string }) {
  const res = await apiPost<AuthResponse>("/auth/login/", payload);
  authTokenStore.set(res.token);
  return res;
}

export async function logout() {
  try {
    await apiPost<{ detail: string }>("/auth/logout/", {});
  } finally {
    authTokenStore.set(null);
  }
}

export async function me() {
  return apiGet<AuthUser>("/auth/me/");
}

export async function requestOtp(payload: { email: string; purpose: "verify" | "reset" }) {
  return apiPost<{ detail: string }>("/auth/otp/request/", payload);
}

export async function verifyOtp(payload: { email: string; code: string; purpose: "verify" | "reset" }) {
  return apiPost<AuthResponse | { detail: string }>("/auth/otp/verify/", payload);
}

export async function forgotPassword(payload: { email: string }) {
  return apiPost<{ detail: string }>("/auth/password/forgot/", payload);
}

export async function resetPassword(payload: { email: string; code: string; new_password: string }) {
  return apiPost<{ detail: string }>("/auth/password/reset/", payload);
}

