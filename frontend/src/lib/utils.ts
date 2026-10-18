import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind classes safely, resolving conflicts. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** Format a number as Indian currency (₹1,23,456). */
export function formatINR(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

/** Format a date relative to today ("3 days left" / "2 days ago"). */
export function formatDaysLeft(dateStr: string | null): string {
  if (!dateStr) return "N/A";
  const target = new Date(dateStr);
  const today = new Date();
  const diffMs = target.getTime() - today.getTime();
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays > 0) return `${diffDays} days left`;
  if (diffDays === 0) return "Today";
  return `${Math.abs(diffDays)} days ago`;
}

/** Clamp a value between min and max. */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/** Get initials from a full name. */
export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((word) => word[0] ?? "")
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

/** Band colour map for prediction results. */
export const BAND_COLORS = {
  Safe: "text-safe bg-green-50 border-green-200",
  Target: "text-target bg-amber-50 border-amber-200",
  Dream: "text-dream bg-purple-50 border-purple-200",
} as const;

export type Band = keyof typeof BAND_COLORS;
