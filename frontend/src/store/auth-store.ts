import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '@/types';

export const WORKER_USER: User = {
  id: 'usr-worker-01',
  email: 'worker123@ex.com',
  name: 'A. Sharma',
  role: 'worker',
  avatar: 'AS',
  title: 'Risk Ops Worker',
};

export const MANAGER_USER: User = {
  id: 'usr-manager-01',
  email: 'manager123@ex.com',
  name: 'S. Reynolds',
  role: 'manager',
  avatar: 'SR',
  title: 'Manager / Risk Lead',
};

interface AuthStore {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, pass: string) => { success: boolean; user?: User; error?: string };
  logout: () => void;
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthStore>()(persist((set) => ({
  user: null, // by default not logged in, requiring auth or demo sign-in
  isAuthenticated: false,

  login: (email: string, pass: string) => {
    const cleanEmail = email.trim().toLowerCase();
    const cleanPass = pass.trim();

    if (cleanEmail === 'manager123@ex.com' && cleanPass === '123456') {
      set({ user: MANAGER_USER, isAuthenticated: true });
      return { success: true, user: MANAGER_USER };
    }

    if (cleanEmail === 'worker123@ex.com' && cleanPass === '123456') {
      set({ user: WORKER_USER, isAuthenticated: true });
      return { success: true, user: WORKER_USER };
    }

    return { success: false, error: 'Incorrect email or password.' };
  },

  logout: () => {
    set({ user: null, isAuthenticated: false });
  },

  setUser: (user: User | null) => {
    set({ user, isAuthenticated: !!user });
  },
}), {
  name: 'sovia-demo-auth',
  partialize: (state) => ({
    user: state.user,
    isAuthenticated: state.isAuthenticated,
  }),
}));
