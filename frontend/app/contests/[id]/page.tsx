'use client';

import MainLayout from '@/components/codeforge/MainLayout';
import ContestDetailPage from '@/components/codeforge/ContestDetailPage';

export default function ContestDetailRoute({ params }: { params: { id: string } }) {
  return (
    <MainLayout>
      <ContestDetailPage contestId={params.id} />
    </MainLayout>
  );
}
