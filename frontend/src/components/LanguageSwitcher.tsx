"use client";

import { usePathname, useRouter } from "@/i18n/routing";
import { locales, type Locale } from "@/i18n/routing";
import { Globe } from "lucide-react";
import { useState } from "react";

const LOCALE_LABELS: Record<Locale, string> = {
  en: "English",
  te: "తెలుగు",
  hi: "हिन्दी",
};

interface Props {
  currentLocale: Locale;
  compact?: boolean;
}

export default function LanguageSwitcher({ currentLocale, compact = false }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  function switchLocale(locale: Locale) {
    setOpen(false);
    router.replace(pathname, { locale });
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 rounded-md px-2 py-1.5 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
        aria-label="Switch language"
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        <Globe className="h-4 w-4" aria-hidden="true" />
        {!compact && <span>{LOCALE_LABELS[currentLocale]}</span>}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} aria-hidden="true" />
          <div
            className="absolute right-0 z-50 mt-1 min-w-[120px] rounded-lg border bg-popover shadow-md"
            role="listbox"
            aria-label="Select language"
          >
            {locales.map((locale) => (
              <button
                key={locale}
                role="option"
                aria-selected={locale === currentLocale}
                onClick={() => switchLocale(locale)}
                className={`flex w-full items-center gap-2 px-3 py-2 text-sm transition-colors hover:bg-accent first:rounded-t-lg last:rounded-b-lg ${
                  locale === currentLocale ? "bg-accent font-medium" : ""
                }`}
              >
                {LOCALE_LABELS[locale]}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
