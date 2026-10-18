import { redirect } from "next/navigation";

/** Locale root → dashboard. */
export default function LocaleRootPage({ params }: { params: { locale: string } }) {
  redirect(`/${params.locale}/sign-in`);
}
