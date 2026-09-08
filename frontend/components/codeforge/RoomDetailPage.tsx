'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Circle, LogOut, RefreshCw, Users } from 'lucide-react';
import { Spinner, Button } from './SharedComponents';
import CodeEditor from './CodeEditor';
import { useRoom, useJoinRoom, useLeaveRoom } from '@/lib/api/hooks';
import { useRoomSocket } from '@/lib/api/roomSocket';

const DEBOUNCE_MS = 600;

const RoomDetailPage: React.FC<{ roomId: string }> = ({ roomId }) => {
  const router = useRouter();
  const { data: room, isLoading } = useRoom(roomId);
  const joinRoom = useJoinRoom();
  const leaveRoom = useLeaveRoom();
  const [hasJoined, setHasJoined] = useState(false);
  const [joinError, setJoinError] = useState<string | null>(null);

  useEffect(() => {
    if (!roomId || hasJoined) return;
    joinRoom.mutate(roomId, {
      onSuccess: () => setHasJoined(true),
      onError: () =>
        setJoinError('Could not join this room — it may be private and require an invite.'),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roomId]);

  const socket = useRoomSocket(hasJoined ? roomId : undefined);
  const [localCode, setLocalCode] = useState('');
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // The server never echoes a sender's own update, so every incoming
  // `document` here is either the initial snapshot or a genuine remote
  // change — always safe to adopt. There's no conflict resolution beyond
  // that (matching the backend's own last-write-wins model), so a remote
  // edit arriving mid-keystroke can overwrite an unsent local buffer; that's
  // an inherent limit of this protocol, not something to paper over here.
  useEffect(() => {
    if (socket.document) setLocalCode(socket.document.code);
  }, [socket.document]);

  const handleCodeChange = (value: string) => {
    setLocalCode(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      socket.sendDocumentUpdate({ code: value, language: socket.document?.language ?? 'python' });
    }, DEBOUNCE_MS);
  };

  const handleLanguageChange = (language: string) => {
    socket.sendDocumentUpdate({ code: localCode, language });
  };

  if (isLoading || !room) {
    return (
      <div className="flex h-full items-center justify-center bg-[#0B0F17]">
        <Spinner size={28} />
      </div>
    );
  }

  if (joinError) {
    return (
      <div className="flex h-full items-center justify-center bg-[#0B0F17] p-6">
        <div className="max-w-md text-center">
          <p className="text-sm text-rose-400">{joinError}</p>
          <Link
            href="/rooms"
            className="mt-4 inline-block text-sm text-cyan-400 hover:text-cyan-300"
          >
            ← Back to rooms
          </Link>
        </div>
      </div>
    );
  }

  const isViewer = socket.role === 'viewer';

  return (
    <div className="flex h-full flex-col overflow-hidden bg-[#0B0F17] p-6">
      <div className="mb-4 flex items-center gap-4">
        <Link
          href="/rooms"
          className="flex items-center gap-1.5 text-xs font-medium text-gray-500 hover:text-gray-300"
        >
          <ArrowLeft size={13} /> Back
        </Link>
        <h1 className="flex-1 text-lg font-bold text-white">{room.title}</h1>

        <span className="flex items-center gap-1.5 text-xs text-gray-500">
          <Users size={13} />
          {socket.onlineCount} online
        </span>

        <span
          className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${
            socket.status === 'open'
              ? 'border-emerald-700 bg-emerald-900/30 text-emerald-400'
              : socket.status === 'connecting'
                ? 'border-amber-700 bg-amber-900/30 text-amber-400'
                : 'border-rose-700 bg-rose-900/30 text-rose-400'
          }`}
        >
          <Circle size={7} className="fill-current" />
          {socket.status === 'open' ? 'live' : socket.status}
        </span>

        {socket.status !== 'open' && socket.status !== 'connecting' && (
          <button
            onClick={socket.reconnect}
            className="flex items-center gap-1.5 rounded-lg bg-gray-800 px-3 py-1.5 text-xs font-medium text-gray-300 hover:bg-gray-700"
          >
            <RefreshCw size={13} />
            Reconnect
          </button>
        )}

        <Button
          variant="secondary"
          size="sm"
          onClick={() => leaveRoom.mutate(roomId, { onSuccess: () => router.push('/rooms') })}
        >
          <LogOut size={14} />
          Leave
        </Button>
      </div>

      {isViewer && (
        <div className="mb-3 rounded-lg border border-amber-800/40 bg-amber-950/20 px-4 py-2 text-xs text-amber-400">
          You have viewer access — changes you make here won&apos;t be sent to the room.
        </div>
      )}

      {!socket.document ? (
        <div className="flex flex-1 items-center justify-center">
          <Spinner size={28} />
        </div>
      ) : (
        <CodeEditor
          value={localCode}
          onChange={isViewer ? () => {} : handleCodeChange}
          language={socket.document.language || 'python'}
          onLanguageChange={isViewer ? () => {} : handleLanguageChange}
          height="100%"
        />
      )}
    </div>
  );
};

export default RoomDetailPage;
