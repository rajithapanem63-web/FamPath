import { describe, it, expect } from "vitest";
import { cn, formatINR, formatDaysLeft, clamp, getInitials, BAND_COLORS } from "@/lib/utils";

describe("cn()", () => {
  it("merges class names", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("resolves tailwind conflicts", () => {
    // tailwind-merge should keep the last conflicting class
    const result = cn("px-2", "px-4");
    expect(result).toBe("px-4");
  });

  it("handles conditional classes", () => {
    expect(cn("base", false && "skipped", "included")).toBe("base included");
  });
});

describe("formatINR()", () => {
  it("formats integer as Indian rupees", () => {
    const result = formatINR(123456);
    expect(result).toContain("₹");
    expect(result).toContain("1,23,456");
  });

  it("formats zero", () => {
    expect(formatINR(0)).toContain("₹");
  });
});

describe("formatDaysLeft()", () => {
  it("returns N/A for null", () => {
    expect(formatDaysLeft(null)).toBe("N/A");
  });

  it("returns 'Today' for today", () => {
    const today = new Date().toISOString();
    expect(formatDaysLeft(today)).toBe("Today");
  });

  it("returns days ago for past date", () => {
    const past = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString();
    expect(formatDaysLeft(past)).toContain("days ago");
  });

  it("returns days left for future date", () => {
    const future = new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString();
    expect(formatDaysLeft(future)).toContain("days left");
  });
});

describe("clamp()", () => {
  it("clamps below min", () => expect(clamp(-5, 0, 10)).toBe(0));
  it("clamps above max", () => expect(clamp(15, 0, 10)).toBe(10));
  it("returns value in range", () => expect(clamp(5, 0, 10)).toBe(5));
});

describe("getInitials()", () => {
  it("returns two letters for full name", () => {
    expect(getInitials("Rajesh Kumar")).toBe("RK");
  });

  it("returns one letter for single name", () => {
    expect(getInitials("Priya")).toBe("P");
  });

  it("truncates to 2 chars", () => {
    expect(getInitials("A B C D")).toBe("AB");
  });
});

describe("BAND_COLORS", () => {
  it("has Safe, Target, Dream entries", () => {
    expect(BAND_COLORS).toHaveProperty("Safe");
    expect(BAND_COLORS).toHaveProperty("Target");
    expect(BAND_COLORS).toHaveProperty("Dream");
  });
});
