/**
 * next-intl routing configuration for v3.15.x.
 * NOTE: defineRouting() was added in next-intl v3.22+.
 * This project uses v3.15.3, which uses createSharedPathnamesNavigation directly.
 */
import { createSharedPathnamesNavigation } from "next-intl/navigation";

export const locales = ["en", "te", "hi"] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = "en";

/** Plain config object used by next.config.mjs plugin and layout. */
export const routing = {
  locales,
  defaultLocale,
  localePrefix: "always" as const,
};

/** Typed navigation helpers — use these instead of next/link etc. */
export const { Link, redirect, usePathname, useRouter } =
  createSharedPathnamesNavigation({ locales, localePrefix: "always" });
