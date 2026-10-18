"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/routing";
import { resetPassword } from "@/lib/auth";
import { getErrorCode } from "@/lib/api";

const schema = z.object({
  new_password: z
    .string()
    .min(8, "Minimum 8 characters")
    .regex(/[A-Z]/, "Must contain an uppercase letter")
    .regex(/[0-9]/, "Must contain a number"),
  confirm_password: z.string(),
}).refine((d) => d.new_password === d.confirm_password, {
  message: "Passwords do not match",
  path: ["confirm_password"],
});
type FormValues = z.infer<typeof schema>;

export default function ResetPasswordPage() {
  const t = useTranslations("auth.resetPassword");
  const tCommon = useTranslations("common");
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [success, setSuccess] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(data: FormValues) {
    setServerError(null);
    if (!token) {
      setServerError("Reset link is invalid or missing. Please request a new one.");
      return;
    }
    try {
      await resetPassword(token, data.new_password);
      setSuccess(true);
    } catch (err) {
      const code = getErrorCode(err);
      if (code === "RESET_TOKEN_INVALID") {
        setServerError("This reset link has expired or already been used. Please request a new one.");
      } else {
        setServerError("Password reset failed. Please try again.");
      }
    }
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-md bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
          <div className="text-5xl mb-4">🔐</div>
          <h2 className="text-lg font-semibold text-gray-900">{t("successMessage")}</h2>
          <p className="text-sm text-muted-foreground mt-2 mb-6">
            Your password has been updated. You can now sign in with your new password.
          </p>
          <Link
            href="/sign-in"
            className="inline-block bg-brand-600 text-white rounded-lg px-6 py-2.5 text-sm font-semibold hover:bg-brand-700 transition"
          >
            Sign in
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-brand-600">FamPath</h1>
        </div>
        <h2 className="text-xl font-semibold mb-6">{t("title")}</h2>

        {serverError && (
          <div role="alert" className="mb-4 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
            {serverError}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
          <div>
            <label htmlFor="new_password" className="block text-sm font-medium mb-1">
              {t("passwordLabel")}
            </label>
            <input
              id="new_password"
              type="password"
              autoComplete="new-password"
              className="w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              {...register("new_password")}
              aria-invalid={!!errors.new_password}
            />
            {errors.new_password && (
              <p className="mt-1 text-xs text-red-600">{errors.new_password.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="confirm_password" className="block text-sm font-medium mb-1">
              Confirm new password
            </label>
            <input
              id="confirm_password"
              type="password"
              autoComplete="new-password"
              className="w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              {...register("confirm_password")}
              aria-invalid={!!errors.confirm_password}
            />
            {errors.confirm_password && (
              <p className="mt-1 text-xs text-red-600">{errors.confirm_password.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-brand-600 text-white rounded-lg py-2.5 text-sm font-semibold hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-ring transition-colors"
          >
            {isSubmitting ? tCommon("loading") : t("submitButton")}
          </button>
        </form>
      </div>
    </div>
  );
}
