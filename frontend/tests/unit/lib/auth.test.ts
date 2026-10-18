import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock the api module
vi.mock("@/lib/api", () => ({
  post: vi.fn(),
  get: vi.fn(),
  getErrorCode: (err: unknown) => "UNKNOWN_ERROR",
}));

import { setAccessToken, getAccessToken, clearAccessToken } from "@/lib/auth";
import * as api from "@/lib/api";

describe("Token storage", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("stores and retrieves access token", () => {
    setAccessToken("test-token-123");
    expect(getAccessToken()).toBe("test-token-123");
  });

  it("clears access token", () => {
    setAccessToken("test-token-123");
    clearAccessToken();
    expect(getAccessToken()).toBeNull();
  });

  it("returns null when no token", () => {
    expect(getAccessToken()).toBeNull();
  });
});

describe("login()", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("stores access token on success", async () => {
    const mockUser = {
      id: "uuid-1",
      email: "test@example.com",
      full_name: "Test User",
      role: "student",
      status: "active",
      preferred_locale: "en",
      created_at: "2024-01-01T00:00:00Z",
    };

    vi.mocked(api.post).mockResolvedValueOnce({
      access_token: "jwt-access-token",
      token_type: "bearer",
      user: mockUser,
    });

    const { login } = await import("@/lib/auth");
    const user = await login("test@example.com", "TestPass1");

    expect(user.email).toBe("test@example.com");
    expect(getAccessToken()).toBe("jwt-access-token");
  });

  it("does not store token on failure", async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error("Unauthorized"));

    const { login } = await import("@/lib/auth");
    await expect(login("bad@email.com", "wrong")).rejects.toThrow();
    expect(getAccessToken()).toBeNull();
  });
});
