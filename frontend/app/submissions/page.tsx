'use client';

import MainLayout from '@/components/codeforge/MainLayout';
import SubmissionsListPage from '@/components/codeforge/SubmissionsListPage';

export default function SubmissionsRoute() {
  return (
    <MainLayout>
      <SubmissionsListPage />
    </MainLayout>
  );
}
