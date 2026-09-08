'use client';

import MainLayout from '@/components/codeforge/MainLayout';
import SubmissionResultsPage from '@/components/codeforge/SubmissionResultsPage';

export default function SubmissionDetailRoute({ params }: { params: { id: string } }) {
  return (
    <MainLayout>
      <SubmissionResultsPage submissionId={params.id} />
    </MainLayout>
  );
}
