/**
 * Playwright auth helpers: create test user via API and get a token.
 * Used to log in quickly via API rather than through the UI.
 */
import { type APIRequestContext } from "@playwright/test";

const API_BASE = process.env["E2E_API_URL"] ?? "http://localhost:8000";

export interface TestUser {
  email: string;
  password: string;
  accessToken: string;
}

let userCounter = 0;

/** Create a unique student test user via the API, activate them, and return credentials. */
export async function createTestUser(
  request: APIRequestContext,
  role: "student" | "parent" = "student"
): Promise<TestUser> {
  userCounter++;
  const email = `e2e_${Date.now()}_${userCounter}@fampath-test.invalid`;
  const password = "E2eTest1!";

  // Register
  const registerResp = await request.post(`${API_BASE}/api/v1/auth/register`, {
    data: { email, password, full_name: "E2E Test User", role, preferred_locale: "en" },
  });

  if (!registerResp.ok()) {
    throw new Error(`Registration failed: ${await registerResp.text()}`);
  }

  // Directly activate via a test endpoint (only available in testing env)
  // In a real CI environment this would be done via a test DB helper
  // For now, we rely on a test-only activation endpoint
  const activateResp = await request.post(`${API_BASE}/api/v1/auth/test/activate`, {
    data: { email },
  });

  // If test endpoint not available, try login anyway (may fail if not activated)
  const loginResp = await request.post(`${API_BASE}/api/v1/auth/login`, {
    data: { email, password },
  });

  if (!loginResp.ok()) {
    // Return without token — test will skip or handle
    return { email, password, accessToken: "" };
  }

  const { access_token } = await loginResp.json() as { access_token: string };
  return { email, password, accessToken: access_token };
}
