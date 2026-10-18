import { redirect } from "next/navigation";

/** Root redirect → default locale sign-in page. */
export default function RootPage() {
  redirect("/en/sign-in");
}
