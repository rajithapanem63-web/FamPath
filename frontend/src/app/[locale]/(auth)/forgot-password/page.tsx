"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/routing";
import { forgotPassword } from "@/lib/auth";

const schema = z.object({
  email: z.string().email("Valid email required"),
});
type FormValues = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  const t = useTranslations("auth.forgotPassword");
  const tCommon = useTranslations("common");
  const [sent, setSent] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(data: FormValues) {
    await forgotPassword(data.email);
    setSent(true);
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-brand-600">FamPath</h1>
        </div>

        <h2 className="text-xl font-semibold mb-2">{t("title")}</h2>
        <p className="text-sm text-muted-foreground mb-6">
          Enter your email and we'll send a reset link if an account exists.
        </p>

        {sent ? (
          <div className="text-center space-y-4">
            <div className="text-5xl">📬</div>
            <p className="text-sm font-medium text-green-700 bg-green-50 border border-green-200 rounded-lg p-3">
              {t("successMessage")}
            </p>
            <Link href="/sign-in" className="block text-sm text-brand-600 hover:underline mt-4">
              Back to sign in
            </Link>
          </div>
        ) : (
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

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-brand-600 text-white rounded-lg py-2.5 text-sm font-semibold hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-ring transition-colors"
            >
              {isSubmitting ? tCommon("loading") : t("submitButton")}
            </button>

            <p className="text-center text-sm text-muted-foreground">
              <Link href="/sign-in" className="text-brand-600 hover:underline">
                Back to sign in
              </Link>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}
