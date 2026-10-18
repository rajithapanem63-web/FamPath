/**
 * E2E: Student sign-up and email verification journey.
 * Journey #1 from the testing spec.
 */
import { test, expect } from "@playwright/test";

test.describe("Sign-up journey", () => {
  test("should render sign-up form with all required fields", async ({ page }) => {
    await page.goto("/en/sign-up");

    // Check page title accessible
    await expect(page.getByRole("heading", { level: 2 })).toBeVisible();

    // All form fields present
    await expect(page.getByLabel(/full name/i)).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole("combobox", { name: /i am/i })).toBeVisible();
  });

  test("should show validation errors for empty form submission", async ({ page }) => {
    await page.goto("/en/sign-up");
    await page.getByRole("button", { name: /create account/i }).click();
    // Validation errors should appear
    await expect(page.getByText(/required/i).first()).toBeVisible();
  });

  test("should show error for weak password", async ({ page }) => {
    await page.goto("/en/sign-up");
    await page.getByLabel(/email/i).fill("test@example.com");
    await page.getByLabel(/password/i).fill("weak");
    await page.getByLabel(/full name/i).fill("Test User");
    await page.getByRole("button", { name: /create account/i }).click();
    await expect(page.getByText(/minimum 8/i)).toBeVisible();
  });

  test("should navigate to sign-in from sign-up page", async ({ page }) => {
    await page.goto("/en/sign-up");
    await page.getByRole("link", { name: /sign in/i }).click();
    await expect(page).toHaveURL(/sign-in/);
  });

  test("sign-up page should pass basic accessibility checks", async ({ page }) => {
    const { checkA11y, injectAxe } = await import("axe-playwright");
    await page.goto("/en/sign-up");
    await injectAxe(page);
    await checkA11y(page, undefined, {
      detailedReport: false,
      axeOptions: { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa"] } },
    });
  });
});

test.describe("Sign-in journey", () => {
  test("should render sign-in form", async ({ page }) => {
    await page.goto("/en/sign-in");
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
  });

  test("should show forgot password link", async ({ page }) => {
    await page.goto("/en/sign-in");
    await expect(page.getByRole("link", { name: /forgot password/i })).toBeVisible();
  });

  test("should show error for invalid credentials", async ({ page }) => {
    await page.goto("/en/sign-in");
    await page.getByLabel(/email/i).fill("nobody@example.com");
    await page.getByLabel(/password/i).fill("WrongPass1");
    await page.getByRole("button", { name: /sign in/i }).click();
    // Error message should appear
    await expect(
      page.getByRole("alert").or(page.getByText(/invalid/i))
    ).toBeVisible({ timeout: 5000 });
  });
});
