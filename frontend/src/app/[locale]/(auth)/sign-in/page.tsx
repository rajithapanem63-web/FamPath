"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/routing";
import { Link } from "@/i18n/routing";
import { login } from "@/lib/auth";
import { getErrorCode } from "@/lib/api";

const schema = z.object({
  email: z.string().email("Valid email required"),
  password: z.string().min(1, "Password required"),
});
type FormValues = z.infer<typeof schema>;

export default function SignInPage() {
  const t = useTranslations("auth.signIn");
  const tCommon = useTranslations("common");
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  async function onSubmit(data: FormValues) {
    setServerError(null);
    try {
      const user = await login(data.email, data.password);
      // Persist user in global auth store
      const { useAuthStore } = await import("@/stores/authStore");
      useAuthStore.getState().setUser(user);
      router.push("/dashboard");
    } catch (err) {
      const code = getErrorCode(err);
      if (code === "INVALID_CREDENTIALS") {
        setServerError(t("errors.INVALID_CREDENTIALS"));
      } else if (code === "EMAIL_NOT_VERIFIED") {
        setServerError(t("errors.EMAIL_NOT_VERIFIED"));
      } else if (code === "ACCOUNT_LOCKED") {
        setServerError(t("errors.ACCOUNT_LOCKED"));
      } else if (code === "RATE_LIMIT_EXCEEDED") {
        setServerError(t("errors.RATE_LIMIT_EXCEEDED"));
      } else {
        setServerError("Sign in failed. Please try again.");
      }
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-brand-600">FamPath</h1>
        </div>

        <h2 className="text-xl font-semibold mb-6">{t("title")}</h2>

        {serverError && (
          <div
            role="alert"
            className="mb-4 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700"
          >
            {serverError}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1">
              {t("emailLabel")}
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              className="w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              {...register("email")}
              aria-invalid={!!errors.email}
            />
            {errors.email && (
              <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>
            )}
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label htmlFor="password" className="block text-sm font-medium">
                {t("passwordLabel")}
              </label>
              <Link
                href="/forgot-password"
                className="text-xs text-brand-600 hover:underline"
              >
                {t("forgotPassword")}
              </Link>
            </div>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              className="w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              {...register("password")}
              aria-invalid={!!errors.password}
            />
            {errors.password && (
              <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-brand-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
          >
            {isSubmitting ? tCommon("loading") : t("submitButton")}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-muted-foreground">
          {t("noAccount")}{" "}
          <Link href="/sign-up" className="text-brand-600 hover:underline font-medium">
            {t("signUpLink")}
          </Link>
        </div>
      </div>
    </div>
  );
}