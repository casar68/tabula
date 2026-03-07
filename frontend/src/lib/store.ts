import { create } from "zustand";
import type { Selection } from "./types";

interface SelectionStore {
  selections: Selection[];
  addSelection: (sel: Selection) => void;
  removeSelection: (id: string) => void;
  updateSelection: (id: string, updates: Partial<Selection>) => void;
  clearSelections: () => void;
  setSelections: (sels: Selection[]) => void;
}

export const useSelectionStore = create<SelectionStore>((set) => ({
  selections: [],
  addSelection: (sel) =>
    set((state) => ({ selections: [...state.selections, sel] })),
  removeSelection: (id) =>
    set((state) => ({
      selections: state.selections.filter((s) => s.id !== id),
    })),
  updateSelection: (id, updates) =>
    set((state) => ({
      selections: state.selections.map((s) =>
        s.id === id ? { ...s, ...updates } : s
      ),
    })),
  clearSelections: () => set({ selections: [] }),
  setSelections: (sels) => set({ selections: sels }),
}));
