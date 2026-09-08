'use client';

import React, { useEffect, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Save, KeyRound } from 'lucide-react';
import MainLayout from '@/components/codeforge/MainLayout';
import { usersApi } from '@/lib/api/endpoints';
import { apiErrorMessage } from '@/lib/api/client';
import { useAuthStore } from '@/store/auth';

export default function SettingsPage() {
  const { user, setUser } = useAuthStore();
  const [fullName, setFullName] = useState('');
  const [bio, setBio] = useState('');
  const [profileMessage, setProfileMessage] = useState<string | null>(null);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);

  useEffect(() => {
    setFullName(user?.full_name ?? '');
    setBio(user?.bio ?? '');
  }, [user]);

  const profileMutation = useMutation({
    mutationFn: () => usersApi.updateProfile({ full_name: fullName, bio }),
    onSuccess: (updated) => {
      setUser(updated);
      setProfileMessage('Profile updated.');
    },
    onError: (err) => setProfileMessage(apiErrorMessage(err)),
  });

  const passwordMutation = useMutation({
    mutationFn: () =>
      usersApi.changePassword({ current_password: currentPassword, new_password: newPassword }),
    onSuccess: () => {
      setPasswordMessage('Password changed.');
      setCurrentPassword('');
      setNewPassword('');
    },
    onError: (err) => setPasswordMessage(apiErrorMessage(err)),
  });

  return (
    <MainLayout>
      <div className="min-h-full bg-[#0B0F17] p-6">
        <div className="mx-auto max-w-xl space-y-6">
          <h1 className="text-2xl font-bold text-white">Settings</h1>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              setProfileMessage(null);
              profileMutation.mutate();
            }}
            className="space-y-4 rounded-lg border border-gray-800 bg-gray-900/60 p-6"
          >
            <h2 className="text-sm font-semibold text-white">Profile</h2>
            <div>
              <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-gray-500">
                Display name
              </label>
              <input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full rounded-lg border border-gray-800 bg-gray-950 px-3 py-2 text-sm text-white focus:border-cyan-600 focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-gray-500">
                Bio
              </label>
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                rows={3}
                className="w-full resize-none rounded-lg border border-gray-800 bg-gray-950 px-3 py-2 text-sm text-white focus:border-cyan-600 focus:outline-none"
              />
            </div>
            {profileMessage && <p className="text-xs text-cyan-400">{profileMessage}</p>}
            <button
              type="submit"
              disabled={profileMutation.isPending}
              className="flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 text-sm font-semibold text-white hover:bg-cyan-500 disabled:opacity-50"
            >
              <Save size={15} />
              Save profile
            </button>
          </form>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              setPasswordMessage(null);
              passwordMutation.mutate();
            }}
            className="space-y-4 rounded-lg border border-gray-800 bg-gray-900/60 p-6"
          >
            <h2 className="text-sm font-semibold text-white">Change password</h2>
            <input
              type="password"
              required
              minLength={8}
              placeholder="Current password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-800 bg-gray-950 px-3 py-2 text-sm text-white focus:border-cyan-600 focus:outline-none"
            />
            <input
              type="password"
              required
              minLength={8}
              placeholder="New password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-800 bg-gray-950 px-3 py-2 text-sm text-white focus:border-cyan-600 focus:outline-none"
            />
            {passwordMessage && <p className="text-xs text-cyan-400">{passwordMessage}</p>}
            <button
              type="submit"
              disabled={passwordMutation.isPending}
              className="flex items-center gap-2 rounded-lg bg-gray-800 px-4 py-2 text-sm font-semibold text-gray-200 hover:bg-gray-700 disabled:opacity-50"
            >
              <KeyRound size={15} />
              Update password
            </button>
          </form>
        </div>
      </div>
    </MainLayout>
  );
}
