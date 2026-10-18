import type { Metadata, Viewport } from "next";
import { notFound } from "next/navigation";
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";
import { routing } from "@/i18n/routing";
import type { Locale } from "@/i18n/routing";
import Providers from "@/components/Providers";
import "../globals.css";

export const metadata: Metadata = {
  title: {
    default: "FamPath – Engineering College Decision Support",
    template: "%s | FamPath",
  },
  description:
    "AI-powered, family-first decision support for engineering college selection in India.",
  manifest: "/manifest.json",
  appleWebApp: { capable: true, statusBarStyle: "default", title: "FamPath" },
  icons: { icon: "/icons/icon-192x192.png", apple: "/icons/icon-192x192.png" },
};

export const viewport: Viewport = {
  themeColor: "#2563EB",
  width: "device-width",
  initialScale: 1,
};

interface Props {
  children: React.ReactNode;
  params: { locale: string };
}

export default async function LocaleLayout({ children, params }: Props) {
  const { locale } = params;

  // Validate locale
  if (!routing.locales.includes(locale as Locale)) {
    notFound();
  }

  // In next-intl 3.15.x, getMessages() reads locale from request context (no argument needed)
  const messages = await getMessages();

  return (
    <html lang={locale} suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans antialiased">
        <NextIntlClientProvider locale={locale} messages={messages}>
          <Providers>{children}</Providers>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}

// Generate static paths for all locales
export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}
