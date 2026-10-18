import { getRequestConfig } from "next-intl/server";
import { routing } from "./routing";
import type { Locale } from "./routing";

export default getRequestConfig(async ({ locale }) => {
  // Validate that the incoming locale is supported
  if (!routing.locales.includes(locale as Locale)) {
    const { notFound } = await import("next/navigation");
    notFound();
  }

  return {
    messages: (
      await import(`./messages/${locale}.json`)
    ).default,
  };
});
