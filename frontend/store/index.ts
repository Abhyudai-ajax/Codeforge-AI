import { create } from 'zustand';

/**
 * Global State Management
 * Zustand stores for application state
 */

interface AppStore {
  // Example state
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  isLoading: false,
  setIsLoading: (loading: boolean) => set({ isLoading: loading }),
}));
