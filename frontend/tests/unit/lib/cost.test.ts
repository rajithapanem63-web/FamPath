import { describe, it, expect } from "vitest";

/**
 * Frontend EMI calculator tests (mirrors backend logic for client-side use).
 */
function calculateEmi(principal: number, annualRatePct: number, tenureMonths: number): number {
  if (principal <= 0 || tenureMonths <= 0) return 0;
  const r = annualRatePct / 12 / 100;
  if (r === 0) return principal / tenureMonths;
  return principal * r * Math.pow(1 + r, tenureMonths) / (Math.pow(1 + r, tenureMonths) - 1);
}

describe("EMI calculator (frontend)", () => {
  it("calculates standard EMI correctly", () => {
    const emi = calculateEmi(400000, 8.5, 60);
    expect(emi).toBeGreaterThan(8000);
    expect(emi).toBeLessThan(8500);
  });

  it("returns 0 for zero principal", () => {
    expect(calculateEmi(0, 8.5, 60)).toBe(0);
  });

  it("returns principal/tenure for zero interest", () => {
    expect(calculateEmi(60000, 0, 12)).toBeCloseTo(5000, 0);
  });

  it("higher rate = higher EMI", () => {
    const low = calculateEmi(100000, 7, 36);
    const high = calculateEmi(100000, 12, 36);
    expect(high).toBeGreaterThan(low);
  });

  it("longer tenure = lower EMI", () => {
    const short = calculateEmi(100000, 8.5, 24);
    const long = calculateEmi(100000, 8.5, 60);
    expect(long).toBeLessThan(short);
  });
});
