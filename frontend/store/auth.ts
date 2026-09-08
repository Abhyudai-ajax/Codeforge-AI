'use client';

import { create } from 'zustand';
import { tokenStorage } from '@/lib/api/client';
import type { UserResponse } from '@/lib/api/types';

interface AuthState {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isHydrated: boolean;
  hydrate: () => void;
  setUser: (user: UserResponse | null) => void;
  login: (accessToken: string, refreshToken: string, user: UserResponse) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isHydrated: false,

  hydrate: () => {
    const hasToken = !!tokenStorage.getAccessToken();
    set({ isAuthenticated: hasToken, isHydrated: true });
  },

  setUser: (user) => set({ user, isAuthenticated: !!user }),

  login: (accessToken, refreshToken, user) => {
    tokenStorage.setTokens(accessToken, refreshToken);
    set({ user, isAuthenticated: true, isHydrated: true });
  },

  logout: () => {
    tokenStorage.clear();
    set({ user: null, isAuthenticated: false });
  },
}));
