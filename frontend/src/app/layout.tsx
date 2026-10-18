/**
 * Root layout — wraps the entire app.
 * The real UI layout lives in src/app/[locale]/layout.tsx.
 * This file simply satisfies Next.js App Router's requirement that every
 * page.tsx at the root level has a matching layout.tsx.
 */
export const metadata = {
  title: "FamPath",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html>
      <body>{children}</body>
    </html>
  );
}
