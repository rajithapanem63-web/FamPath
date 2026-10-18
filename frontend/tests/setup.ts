import "@testing-library/jest-dom";
import { cleanup } from "@testing-library/react";
import { afterEach, beforeAll, afterAll, vi } from "vitest";

// Clean up after each test
afterEach(() => {
  cleanup();
});

// Mock next-intl for unit tests
vi.mock("next-intl", () => ({
  useTranslations: (namespace?: string) => (key: string) => `${namespace ? namespace + "." : ""}${key}`,
  useLocale: () => "en",
  NextIntlClientProvider: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock our routing module
vi.mock("@/i18n/routing", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  usePathname: () => "/",
  Link: ({ children, href }: { children: React.ReactNode; href: string }) =>
    ({ type: "a", props: { href, children } } as unknown as JSX.Element),
  redirect: vi.fn(),
  routing: { locales: ["en", "te", "hi"], defaultLocale: "en" },
}));

// Suppress console.error for React testing warnings
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: unknown[]) => {
    if (typeof args[0] === "string" && args[0].includes("Warning:")) return;
    originalError(...args);
  };
});

afterAll(() => {
  console.error = originalError;
});
