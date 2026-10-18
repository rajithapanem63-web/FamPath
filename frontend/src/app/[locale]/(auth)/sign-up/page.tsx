"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/routing";
import { register as registerUser } from "@/lib/auth";
import { getErrorCode } from "@/lib/api";

const schema = z.object({
  email: z.string().email("Valid email required"),
  password: z
    .string()
    .min(8, "Minimum 8 characters")
    .regex(/[A-Z]/, "Must contain an uppercase letter")
    .regex(/[0-9]/, "Must contain a number"),
  full_name: z.string().min(1, "Name required"),
  role: z.enum(["student", "parent", "counsellor"]),
  preferred_locale: z.enum(["en", "te", "hi"]),
});
type FormValues = z.infer<typeof schema>;

export default function SignUpPage() {
  const t = useTranslations("auth.signUp");
  const [success, setSuccess] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { role: "student", preferred_locale: "en" },
  });

  async function onSubmit(data: FormValues) {
    setServerError(null);
    try {
      await registerUser(data);
      setSuccess(true);
    } catch (err) {
      const code = getErrorCode(err);
      setServerError(
        code === "EMAIL_ALREADY_REGISTERED"
          ? t("errors.EMAIL_ALREADY_REGISTERED")
          : "Registration failed. Please try again."
      );
    }
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-md bg-white rounded-xl shadow-sm border p-8 text-center">
          <div className="text-5xl mb-4">🎉</div>
          <h2 className="text-xl font-semibold mb-2">Account Created!</h2>
          <p className="text-gray-600 text-sm mb-6">
            Your account is active. You can now sign in directly.
          </p>
          <Link
            href="/sign-in"
            className="inline-block w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-blue-700 transition"
          >
            Go to Sign In
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
            <label htmlFor="full_name" className="block text-sm font-medium mb-1">
              {t("fullNameLabel")}
            </label>
            <input
              id="full_name"
              type="text"
              autoComplete="name"
              className="w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              {...register("full_name")}
              aria-invalid={!!errors.full_name}
            />
            {errors.full_name && (
              <p className="mt-1 text-xs text-red-600">{errors.full_name.message}</p>
            )}
          </div>

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
            <label htmlFor="password" className="block text-sm font-medium mb-1">
              {t("passwordLabel")}
            </label>
            <input
              id="password"
              type="password"
              autoComplete="new-password"
              className="w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              {...register("password")}
              aria-invalid={!!errors.password}
              aria-describedby="password-hint"
            />
            <p id="password-hint" className="mt-1 text-xs text-muted-foreground">
              {t("passwordHint")}
            </p>
            {errors.password && (
              <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="role" className="block text-sm font-medium mb-1">
              {t("roleLabel")}
            </label>
            <select
              id="role"
              className="w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring bg-white"
              {...register("role")}
            >
              <option value="student">{t("roleStudent")}</option>
              <option value="parent">{t("roleParent")}</option>
              <option value="counsellor">{t("roleCounsellor")}</option>
            </select>
          </div>

          <div>
            <label htmlFor="preferred_locale" className="block text-sm font-medium mb-1">
              {t("localeLabel")}
            </label>
            <select
              id="preferred_locale"
              className="w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring bg-white"
              {...register("preferred_locale")}
            >
              <option value="en">English</option>
              <option value="te">తెలుగు</option>
              <option value="hi">हिन्दी</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-brand-600 text-white py-2.5 text-sm font-semibold hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-60 transition-colors"
          >
            {isSubmitting ? "Creating account…" : t("submitButton")}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          {t("haveAccount")}{" "}
          <Link href="/sign-in" className="text-brand-600 font-medium hover:underline">
            {t("signInLink")}
          </Link>
        </p>
      </div>
    </div>
  );
}
