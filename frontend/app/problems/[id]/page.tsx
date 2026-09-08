'use client';

import MainLayout from '@/components/codeforge/MainLayout';
import ProblemWorkspacePage from '@/components/codeforge/ProblemWorkspacePage';

export default function ProblemRoute({ params }: { params: { id: string } }) {
  return (
    <MainLayout>
      <ProblemWorkspacePage problemId={params.id} />
    </MainLayout>
  );
}
