'use client';

import MainLayout from '@/components/codeforge/MainLayout';
import InterviewSessionPage from '@/components/codeforge/InterviewSessionPage';

export default function InterviewSessionRoute({ params }: { params: { id: string } }) {
  return (
    <MainLayout>
      <InterviewSessionPage sessionId={params.id} />
    </MainLayout>
  );
}
