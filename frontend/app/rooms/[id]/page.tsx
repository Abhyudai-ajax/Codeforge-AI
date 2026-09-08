'use client';

import MainLayout from '@/components/codeforge/MainLayout';
import RoomDetailPage from '@/components/codeforge/RoomDetailPage';

export default function RoomDetailRoute({ params }: { params: { id: string } }) {
  return (
    <MainLayout>
      <RoomDetailPage roomId={params.id} />
    </MainLayout>
  );
}
