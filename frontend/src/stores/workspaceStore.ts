/**
 * Zustand workspace store: current workspace and shortlist state.
 */
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

interface Workspace {
  id: string;
  name: string;
  owner_id: string;
  status: string;
}

interface WorkspaceState {
  workspace: Workspace | null;
  setWorkspace: (ws: Workspace | null) => void;
  clear: () => void;
}

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({
      workspace: null,
      setWorkspace: (workspace) => set({ workspace }),
      clear: () => set({ workspace: null }),
    }),
    {
      name: "fampath-workspace",
      storage: createJSONStorage(() =>
        typeof window !== "undefined" ? localStorage : {
          getItem: () => null,
          setItem: () => {},
          removeItem: () => {},
        }
      ),
    }
  )
);
