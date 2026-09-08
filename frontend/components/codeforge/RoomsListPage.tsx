'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Users, Lock, Globe, Plus } from 'lucide-react';
import { Button, Spinner, EmptyState } from './SharedComponents';
import { useRooms, useCreateRoom } from '@/lib/api/hooks';
import { apiErrorMessage } from '@/lib/api/client';

const RoomsListPage: React.FC = () => {
  const router = useRouter();
  const { data, isLoading } = useRooms();
  const createRoom = useCreateRoom();
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [isPublic, setIsPublic] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = () => {
    setError(null);
    createRoom.mutate(
      { title, is_public: isPublic },
      {
        onSuccess: (room) => router.push(`/rooms/${room.id}`),
        onError: (err) => setError(apiErrorMessage(err, 'Could not create the room.')),
      }
    );
  };

  return (
    <div className="min-h-full space-y-6 bg-[#0B0F17] p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-white">
            <Users size={22} className="text-cyan-400" />
            Coding rooms
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Live, shared code editors — changes sync to everyone in the room.
          </p>
        </div>
        <Button onClick={() => setShowForm((v) => !v)}>
          <Plus size={16} />
          New room
        </Button>
      </div>

      {showForm && (
        <div className="space-y-3 rounded-lg border border-gray-800 bg-gray-900/60 p-5">
          {error && <p className="text-sm text-rose-400">{error}</p>}
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Room title (min 3 characters)"
            className="w-full rounded-lg border border-gray-800 bg-gray-950 px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-cyan-600 focus:outline-none"
          />
          <label className="flex items-center gap-2 text-sm text-gray-400">
            <input
              type="checkbox"
              checked={isPublic}
              onChange={(e) => setIsPublic(e.target.checked)}
            />
            Public — anyone can join without an invite
          </label>
          <Button
            size="sm"
            disabled={title.trim().length < 3 || createRoom.isPending}
            onClick={handleCreate}
          >
            Create & open
          </Button>
        </div>
      )}

      {isLoading ? (
        <div className="flex h-40 items-center justify-center">
          <Spinner />
        </div>
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          title="No rooms yet"
          description="Create one to start a live shared coding session."
        />
      ) : (
        <div className="space-y-2">
          {data.items.map((room) => (
            <Link
              key={room.id}
              href={`/rooms/${room.id}`}
              className="flex items-center gap-3 rounded-lg border border-gray-800 bg-gray-900/60 px-5 py-3.5 transition-colors hover:bg-gray-800/50"
            >
              {room.is_public ? (
                <Globe size={15} className="text-gray-500" />
              ) : (
                <Lock size={15} className="text-gray-500" />
              )}
              <span className="flex-1 text-sm font-medium text-gray-200">{room.title}</span>
              <span className="text-xs uppercase text-gray-600">
                {room.document.language || 'plaintext'}
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default RoomsListPage;
