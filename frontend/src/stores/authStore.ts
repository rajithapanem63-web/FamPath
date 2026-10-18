/**
 * Zustand auth store: current user state and actions.
 * Access token is kept in sessionStorage (not in this store) to avoid XSS leakage.
 */
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { AuthUser } from "@/lib/auth";

interface AuthState {
  user: AuthUser | null;
  isLoading: boolean;
  setUser: (user: AuthUser | null) => void;
  setLoading: (loading: boolean) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isLoading: false,
      setUser: (user) => set({ user }),
      setLoading: (isLoading) => set({ isLoading }),
      clear: () => set({ user: null, isLoading: false }),
    }),
    {
      name: "fampath-auth",
      storage: createJSONStorage(() =>
        typeof window !== "undefined" ? sessionStorage : {
          getItem: () => null,
          setItem: () => {},
          removeItem: () => {},
        }
      ),
      partialize: (state) => ({ user: state.user }),
    }
  )
);
