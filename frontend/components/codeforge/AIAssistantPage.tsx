'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useMutation } from '@tanstack/react-query';
import {
  Sparkles,
  MessageSquareText,
  ClipboardCheck,
  Bug,
  FlaskConical,
  FileText,
} from 'lucide-react';
import { aiApi } from '@/lib/api/endpoints';
import { apiErrorMessage } from '@/lib/api/client';
import { Spinner } from './SharedComponents';

type Mode = 'explain' | 'review' | 'debug' | 'tests' | 'documentation';

const MODES: { id: Mode; label: string; icon: React.ElementType; placeholder: string }[] = [
  {
    id: 'explain',
    label: 'Explain',
    icon: MessageSquareText,
    placeholder: 'Paste code to get a plain-language walkthrough.',
  },
  {
    id: 'review',
    label: 'Review',
    icon: ClipboardCheck,
    placeholder: 'Paste code for a correctness/readability/security review.',
  },
  {
    id: 'debug',
    label: 'Debug',
    icon: Bug,
    placeholder: 'Paste failing code and describe the symptom.',
  },
  {
    id: 'tests',
    label: 'Generate tests',
    icon: FlaskConical,
    placeholder: 'Paste code to generate unit tests for.',
  },
  {
    id: 'documentation',
    label: 'Document',
    icon: FileText,
    placeholder: 'Paste code to generate documentation for.',
  },
];

const AIAssistantPage: React.FC = () => {
  const [mode, setMode] = useState<Mode>('explain');
  const [content, setContent] = useState('');
  const [context, setContext] = useState('');
  const [result, setResult] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => aiApi[mode]({ content, additional_context: context || undefined }),
    onSuccess: (data) => setResult(data.result),
  });

  const active = MODES.find((m) => m.id === mode)!;

  return (
    <div className="min-h-full bg-[#0B0F17] p-6">
      <div className="mx-auto max-w-4xl space-y-6">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-white">
            <Sparkles size={22} className="text-cyan-400" />
            AI assistant
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            General-purpose code assistance, backed by the same AI service used across CodeForge.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {MODES.map((m) => (
            <button
              key={m.id}
              onClick={() => {
                setMode(m.id);
                setResult(null);
              }}
              className={`flex items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors ${
                mode === m.id
                  ? 'bg-cyan-600 text-white'
                  : 'bg-gray-900/70 text-gray-400 hover:bg-gray-800'
              }`}
            >
              <m.icon size={14} />
              {m.label}
            </button>
          ))}
        </div>

        <div className="rounded-lg border border-gray-800 bg-gray-900/60 p-5">
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-gray-500">
            Code
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder={active.placeholder}
            rows={10}
            className="w-full resize-y rounded-lg border border-gray-800 bg-gray-950/60 p-3 font-mono text-sm text-gray-200 placeholder-gray-600 focus:border-cyan-700 focus:outline-none"
          />
          <label className="mb-1.5 mt-4 block text-xs font-semibold uppercase tracking-wider text-gray-500">
            Additional context (optional)
          </label>
          <input
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="e.g. this runs in a hot loop, or: expected O(n) time"
            className="w-full rounded-lg border border-gray-800 bg-gray-950/60 p-2.5 text-sm text-gray-200 placeholder-gray-600 focus:border-cyan-700 focus:outline-none"
          />
          <button
            onClick={() => {
              setResult(null);
              mutation.mutate();
            }}
            disabled={!content.trim() || mutation.isPending}
            className="mt-4 flex items-center gap-2 rounded-lg bg-cyan-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-cyan-500 disabled:cursor-not-allowed disabled:bg-gray-800 disabled:text-gray-500"
          >
            <active.icon size={16} />
            {mutation.isPending ? 'Thinking…' : `Run ${active.label}`}
          </button>
          {mutation.isError && (
            <p className="mt-3 text-sm text-rose-400">
              {apiErrorMessage(mutation.error, 'The AI assistant is unavailable right now.')}
            </p>
          )}
        </div>

        {mutation.isPending && (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        )}

        {result && !mutation.isPending && (
          <div className="markdown-body max-w-none rounded-lg border border-gray-800 bg-gray-900/60 p-6 text-sm text-gray-300">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{result}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIAssistantPage;
