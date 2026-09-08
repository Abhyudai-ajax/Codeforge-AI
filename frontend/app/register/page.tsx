'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { UserPlus, Terminal } from 'lucide-react';
import { authApi } from '@/lib/api/endpoints';
import { apiErrorMessage, tokenStorage } from '@/lib/api/client';
import { useAuthStore } from '@/store/auth';

export default function RegisterPage() {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await authApi.register({ username, email, password });
      const tokens = await authApi.login({ email, password });
      tokenStorage.setTokens(tokens.access_token, tokens.refresh_token);
      const user = await authApi.me();
      login(tokens.access_token, tokens.refresh_token, user);
      router.replace('/');
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not create your account.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0B0F17] px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-cyan-600 font-bold text-white">
            <Terminal size={22} />
          </div>
          <h1 className="text-xl font-bold text-white">
            CodeForge <span className="text-cyan-400">AI</span>
          </h1>
          <p className="text-sm text-gray-500">Create your developer workspace</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="glass-panel space-y-4 rounded-xl border border-gray-800 bg-gray-900/60 p-6"
        >
          {error && (
            <div className="rounded-lg border border-rose-800 bg-rose-950/50 px-3 py-2 text-sm text-rose-400">
              {error}
            </div>
          )}
          <div>
            <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-gray-500">
              Username
            </label>
            <input
              required
              minLength={3}
              pattern="[a-zA-Z0-9_\-]+"
              title="Alphanumeric, underscores and hyphens only"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-lg border border-gray-800 bg-gray-950 px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:border-cyan-600 focus:outline-none focus:ring-1 focus:ring-cyan-600"
              placeholder="jane_dev"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-gray-500">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-gray-800 bg-gray-950 px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:border-cyan-600 focus:outline-none focus:ring-1 focus:ring-cyan-600"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-gray-500">
              Password
            </label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-800 bg-gray-950 px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:border-cyan-600 focus:outline-none focus:ring-1 focus:ring-cyan-600"
              placeholder="At least 8 characters"
            />
          </div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-cyan-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-cyan-500 disabled:cursor-not-allowed disabled:bg-gray-700"
          >
            <UserPlus size={16} />
            {isSubmitting ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-500">
          Already have an account?{' '}
          <Link href="/login" className="font-medium text-cyan-400 hover:text-cyan-300">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
