'use client';

import { useEffect, useState, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import type { User } from '@/types';

interface RoleGateProps {
  children: ReactNode;
  role: User['role'];
}

/**
 * Prototype-only access guard. It runs after Zustand restores the local demo
 * session, preventing role crossover without introducing a backend auth layer.
 */
export default function RoleGate({ children, role }: RoleGateProps) {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const finishHydration = () => setHydrated(true);
    finishHydration();
    const unsubscribe = useAuthStore.persist.onFinishHydration(finishHydration);
    return unsubscribe;
  }, []);

  useEffect(() => {
    if (!hydrated) return;

    if (!isAuthenticated || !user) {
      router.replace('/signin');
      return;
    }

    if (user.role !== role) {
      router.replace(user.role === 'manager' ? '/manager/overview' : '/worker/dashboard');
    }
  }, [hydrated, isAuthenticated, role, router, user]);

  if (!hydrated || !isAuthenticated || !user || user.role !== role) {
    return <div className="min-h-screen bg-[#F4EFE5]" aria-busy="true" />;
  }

  return <>{children}</>;
}
