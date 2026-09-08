'use client';

import React, { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { onUnauthorized } from '@/lib/api/client';
import { useCurrentUser } from '@/lib/api/hooks';

const PUBLIC_ROUTES = ['/login', '/register'];

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, isHydrated, hydrate, setUser } = useAuthStore();
  const isPublicRoute = PUBLIC_ROUTES.includes(pathname);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    const unsubscribe = onUnauthorized(() => router.replace('/login'));
    return () => {
      unsubscribe();
    };
  }, [router]);

  const { data: me } = useCurrentUser(isHydrated && isAuthenticated);

  useEffect(() => {
    if (me) setUser(me);
  }, [me, setUser]);

  useEffect(() => {
    if (!isHydrated) return;
    if (!isAuthenticated && !isPublicRoute) {
      router.replace('/login');
    }
    if (isAuthenticated && isPublicRoute) {
      router.replace('/');
    }
  }, [isHydrated, isAuthenticated, isPublicRoute, router]);

  if (!isHydrated) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0B0F17]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-700 border-t-cyan-500" />
      </div>
    );
  }

  if (!isAuthenticated && !isPublicRoute) {
    return null;
  }

  return <>{children}</>;
}
