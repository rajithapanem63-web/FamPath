import createMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

export default createMiddleware({
  locales: routing.locales,
  defaultLocale: routing.defaultLocale,
  localePrefix: "always",
});

export const config = {
  // Match all pathnames except for:
  // - API routes
  // - Static files (_next, public assets)
  matcher: [
    "/((?!api|_next/static|_next/image|favicon.ico|icons|manifest.json).*)",
  ],
};
