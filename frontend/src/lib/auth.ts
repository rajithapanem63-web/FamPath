/**
 * Auth helpers: token storage (sessionStorage for access token),
 * login/logout helpers, and current-user retrieval.
 */

import { post, get } from "@/lib/api";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string | null;
  role: "student" | "parent" | "counsellor" | "admin";
  status: string;
  preferred_locale: string;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

/** Store the access token in sessionStorage (cleared on tab close). */
export function setAccessToken(token: string): void {
  if (typeof window !== "undefined") {
    sessionStorage.setItem("access_token", token);
  }
}

export function clearAccessToken(): void {
  if (typeof window !== "undefined") {
    sessionStorage.removeItem("access_token");
  }
}

export function getAccessToken(): string | null {
  if (typeof window !== "undefined") {
    return sessionStorage.getItem("access_token");
  }
  return null;
}

export async function login(
  email: string,
  password: string
): Promise<AuthUser> {
  const data = await post<LoginResponse>("/auth/login", { email, password });
  setAccessToken(data.access_token);
  return data.user;
}

export async function logout(): Promise<void> {
  try {
    await post("/auth/logout");
  } finally {
    clearAccessToken();
  }
}

export async function getCurrentUser(): Promise<AuthUser> {
  return get<AuthUser>("/auth/me");
}

export async function register(payload: {
  email: string;
  password: string;
  full_name: string;
  role: string;
  preferred_locale: string;
}): Promise<{ message: string }> {
  return post<{ message: string }>("/auth/register", payload);
}

export async function verifyEmail(token: string): Promise<{ message: string }> {
  return post<{ message: string }>("/auth/verify-email", { token });
}

export async function forgotPassword(email: string): Promise<{ message: string }> {
  return post<{ message: string }>("/auth/forgot-password", { email });
}

export async function resetPassword(
  token: string,
  new_password: string
): Promise<{ message: string }> {
  return post<{ message: string }>("/auth/reset-password", { token, new_password });
}
