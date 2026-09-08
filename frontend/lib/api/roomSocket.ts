'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { tokenStorage } from './client';
import type { RoomDocument, RoomMemberRole } from './types';

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

type ConnectionState = 'connecting' | 'open' | 'closed' | 'error';

interface RoomSocketState {
  status: ConnectionState;
  document: RoomDocument | null;
  version: number;
  role: RoomMemberRole | null;
  onlineCount: number;
  sendDocumentUpdate: (document: RoomDocument) => void;
  sendCursorUpdate: (cursor: { line: number; column: number }) => void;
  reconnect: () => void;
}

/**
 * Drives the room collaboration protocol documented in
 * app/websocket/coding_rooms.py: room_state on connect, then
 * document_update / cursor_update / presence broadcasts.
 *
 * The server force-closes the socket on a document version conflict
 * (two concurrent writers), so this deliberately does not auto-retry —
 * a stale editor silently reconnecting could clobber a teammate's work.
 * The caller gets a `reconnect()` to re-sync deliberately instead.
 */
export function useRoomSocket(roomId: string | undefined): RoomSocketState {
  const [status, setStatus] = useState<ConnectionState>('connecting');
  const [document, setDocument] = useState<RoomDocument | null>(null);
  const [version, setVersion] = useState(0);
  const [role, setRole] = useState<RoomMemberRole | null>(null);
  const [onlineCount, setOnlineCount] = useState(1);
  const socketRef = useRef<WebSocket | null>(null);
  const versionRef = useRef(0);
  const [connectAttempt, setConnectAttempt] = useState(0);

  useEffect(() => {
    if (!roomId) return;
    const token = tokenStorage.getAccessToken();
    if (!token) {
      setStatus('error');
      return;
    }

    setStatus('connecting');
    const socket = new WebSocket(
      `${WS_BASE_URL}/api/v1/rooms/${roomId}/ws?token=${encodeURIComponent(token)}`
    );
    socketRef.current = socket;

    socket.onopen = () => setStatus('open');
    socket.onclose = () => setStatus('closed');
    socket.onerror = () => setStatus('error');
    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        switch (message.type) {
          case 'room_state':
            setDocument(message.document);
            setVersion(message.version);
            versionRef.current = message.version;
            setRole(message.role);
            break;
          case 'document_update':
            setDocument(message.document);
            setVersion(message.version);
            versionRef.current = message.version;
            break;
          case 'presence':
            setOnlineCount((count) =>
              message.state === 'joined' ? count + 1 : Math.max(1, count - 1)
            );
            break;
          default:
            break;
        }
      } catch {
        // Ignore malformed frames rather than crashing the socket handler.
      }
    };

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, [roomId, connectAttempt]);

  const sendDocumentUpdate = useCallback((nextDocument: RoomDocument) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(
      JSON.stringify({
        type: 'document_update',
        document: nextDocument,
        version: versionRef.current,
      })
    );
    // The server never echoes the sender's own update, so advance optimistically.
    versionRef.current += 1;
    setVersion(versionRef.current);
  }, []);

  const sendCursorUpdate = useCallback((cursor: { line: number; column: number }) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ type: 'cursor_update', cursor }));
  }, []);

  const reconnect = useCallback(() => {
    setOnlineCount(1);
    setConnectAttempt((n) => n + 1);
  }, []);

  return {
    status,
    document,
    version,
    role,
    onlineCount,
    sendDocumentUpdate,
    sendCursorUpdate,
    reconnect,
  };
}
