"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/routing";
import { verifyEmail } from "@/lib/auth";

type Status = "verifying" | "success" | "expired" | "error";

export default function VerifyEmailPage() {
  const t = useTranslations("auth.verifyEmail");
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<Status>("verifying");

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setStatus("expired");
      return;
    }
    verifyEmail(token)
      .then(() => setStatus("success"))
      .catch(() => setStatus("expired"));
  }, [searchParams]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-brand-600">FamPath</h1>
        </div>

        {status === "verifying" && (
          <>
            <div className="text-4xl mb-4 animate-pulse">⏳</div>
            <h2 className="text-lg font-semibold text-gray-900">{t("title")}</h2>
            <p className="text-sm text-muted-foreground mt-2">Verifying your email…</p>
          </>
        )}

        {status === "success" && (
          <>
            <div className="text-5xl mb-4">✅</div>
            <h2 className="text-lg font-semibold text-gray-900">{t("successMessage")}</h2>
            <p className="text-sm text-muted-foreground mt-2 mb-6">
              Your account is now active. You can sign in.
            </p>
            <Link
              href="/sign-in"
              className="inline-block bg-brand-600 text-white rounded-lg px-6 py-2.5 text-sm font-semibold hover:bg-brand-700 transition"
            >
              Sign in to FamPath
            </Link>
          </>
        )}

        {(status === "expired" || status === "error") && (
          <>
            <div className="text-5xl mb-4">⚠️</div>
            <h2 className="text-lg font-semibold text-gray-900">{t("expiredMessage")}</h2>
            <p className="text-sm text-muted-foreground mt-2 mb-6">
              The link may have expired or already been used. Request a new one below.
            </p>
            <div className="space-y-3">
              <Link
                href="/sign-up"
                className="inline-block w-full bg-brand-600 text-white rounded-lg px-6 py-2.5 text-sm font-semibold hover:bg-brand-700 transition"
              >
                {t("resendButton")}
              </Link>
              <Link
                href="/sign-in"
                className="block text-sm text-brand-600 hover:underline"
              >
                Back to sign in
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
