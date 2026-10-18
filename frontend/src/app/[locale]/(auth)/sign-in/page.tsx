"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/routing";
import { Link } from "@/i18n/routing";

const schema = z.object({
  email: z.string().email("Valid email required"),
  password: z.string().min(1, "Password required"),
});
type FormValues = z.infer<typeof schema>;

// Get backend URL - works in both client and server components
const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" && window.location.hostname !== "localhost"
    ? "https://fampath-backend.onrender.com"
    : "http://localhost:8000");

export default function SignInPage() {
  const t = useTranslations("auth.signIn");
  const tCommon = useTranslations("common");
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  function fillDemoCredentials() {
    setValue("email", "demo@fampath.com");
    setValue("password", "Demo1234");
    setServerError(null);
  }

  async function onSubmit(data: FormValues) {
    setServerError(null);
    try {
      // Build candidate URLs (configured URL first, then local fallback ports if on localhost)
      const candidateUrls = [API_URL];
      if (API_URL.includes("localhost:8000")) {
        candidateUrls.push(API_URL.replace("localhost:8000", "localhost:8001"));
        candidateUrls.push(API_URL.replace("localhost:8000", "127.0.0.1:8000"));
      } else if (API_URL.includes("localhost:8001")) {
        candidateUrls.push(API_URL.replace("localhost:8001", "localhost:8000"));
        candidateUrls.push(API_URL.replace("localhost:8001", "127.0.0.1:8000"));
      }

      let res: Response | null = null;
      let lastErr: unknown = null;

      for (const baseUrl of candidateUrls) {
        try {
          res = await fetch(`${baseUrl}/api/v1/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ email: data.email.trim(), password: data.password }),
          });
          if (res) break;
        } catch (fetchErr) {
          lastErr = fetchErr;
        }
      }

      if (!res) {
        throw lastErr || new Error("Failed to connect");
      }

      if (!res.ok) {
        const json = await res.json().catch(() => ({}));
        const code = json?.error_code || json?.detail?.error_code || "UNKNOWN";

        if (code === "INVALID_CREDENTIALS") {
          setServerError(t("errors.INVALID_CREDENTIALS"));
        } else if (code === "EMAIL_NOT_VERIFIED") {
          setServerError(t("errors.EMAIL_NOT_VERIFIED"));
        } else if (code === "ACCOUNT_LOCKED") {
          setServerError(t("errors.ACCOUNT_LOCKED"));
        } else if (code === "RATE_LIMIT_EXCEEDED") {
          setServerError(t("errors.RATE_LIMIT_EXCEEDED"));
        } else if (res.status === 422) {
          setServerError("Invalid email or password format.");
        } else {
          setServerError("Sign in failed. Please check your credentials.");
        }
        return;
      }

      const json = await res.json();
      const accessToken: string = json.access_token;
      const user = json.user;

      // Store token
      sessionStorage.setItem("access_token", accessToken);

      // Store user in Zustand store
      try {
        const { useAuthStore } = await import("@/stores/authStore");
        useAuthStore.getState().setUser(user);
      } catch {
        // Store might not load — still redirect
      }

      // Navigate to dashboard
      router.push("/dashboard");
    } catch (err) {
      // Network error
      console.error("Sign in error:", err);
      setServerError(
        `Unable to connect to the backend server (${API_URL}). Please verify that the backend server is running on port 8000.`
      );
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        {/* Logo */}
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-blue-600">FamPath</h1>
          <p className="text-sm text-gray-500 mt-1">
            AI-powered engineering college guidance
          </p>
        </div>

        <h2 className="text-xl font-semibold mb-6">{t("title")}</h2>

        {/* Error banner */}
        {serverError && (
          <div
            role="alert"
            aria-live="polite"
            className="mb-4 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700"
          >
            {serverError}
          </div>
        )}

        <form
          onSubmit={handleSubmit(onSubmit)}
          noValidate
          className="space-y-4"
        >
          {/* Email */}
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              {t("emailLabel")}
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              {...register("email")}
              aria-invalid={!!errors.email}
              aria-describedby={errors.email ? "email-error" : undefined}
            />
            {errors.email && (
              <p id="email-error" className="mt-1 text-xs text-red-600">
                {errors.email.message}
              </p>
            )}
          </div>

          {/* Password */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700"
              >
                {t("passwordLabel")}
              </label>
              <Link
                href="/forgot-password"
                className="text-xs text-blue-600 hover:underline"
              >
                {t("forgotPassword")}
              </Link>
            </div>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              {...register("password")}
              aria-invalid={!!errors.password}
              aria-describedby={errors.password ? "password-error" : undefined}
            />
            {errors.password && (
              <p id="password-error" className="mt-1 text-xs text-red-600">
                {errors.password.message}
              </p>
            )}
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors shadow-sm"
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center gap-2">
                <svg
                  className="animate-spin h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                {tCommon("loading")}
              </span>
            ) : (
              t("submitButton")
            )}
          </button>
        </form>

        {/* Demo Account Quick-Fill */}
        <div className="mt-4 pt-4 border-t border-gray-100 text-center">
          <button
            type="button"
            onClick={fillDemoCredentials}
            className="text-xs text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 rounded-md px-3 py-1.5 transition-colors font-medium border border-blue-200"
          >
            🔑 Fill Demo Credentials (demo@fampath.com)
          </button>
        </div>

        {/* Sign up link */}
        <div className="mt-4 text-center text-sm text-gray-500">
          {t("noAccount")}{" "}
          <Link
            href="/sign-up"
            className="text-blue-600 hover:underline font-medium"
          >
            {t("signUpLink")}
          </Link>
        </div>
      </div>
    </div>
  );
}
