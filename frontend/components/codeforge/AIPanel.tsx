'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Lightbulb, MessageSquareText, ClipboardCheck, Sparkles } from 'lucide-react';
import { useProblemExplain, useProblemHint, useProblemReview } from '@/lib/api/hooks';
import { apiErrorMessage } from '@/lib/api/client';

type Mode = 'hint' | 'explain' | 'review';

const AIPanel: React.FC<{ problemId: string; code: string; language: string }> = ({
  problemId,
  code,
  language,
}) => {
  const [activeMode, setActiveMode] = useState<Mode | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const hint = useProblemHint(problemId);
  const explain = useProblemExplain(problemId);
  const review = useProblemReview(problemId);

  const mutations: Record<Mode, typeof hint> = { hint, explain, review };
  const isLoading = activeMode ? mutations[activeMode].isPending : false;

  const ask = (mode: Mode) => {
    setActiveMode(mode);
    setError(null);
    mutations[mode].mutate(
      { code, language },
      {
        onSuccess: (data) => setResult(data.result),
        onError: (err) =>
          setError(apiErrorMessage(err, 'The AI assistant is unavailable right now.')),
      }
    );
  };

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900/60 p-4">
      <div className="mb-3 flex items-center gap-2">
        <Sparkles size={15} className="text-cyan-400" />
        <span className="text-sm font-semibold text-white">AI assistant</span>
      </div>
      <div className="mb-3 grid grid-cols-3 gap-2">
        <button
          onClick={() => ask('hint')}
          className="flex items-center justify-center gap-1.5 rounded-md border border-gray-800 bg-gray-800/60 py-1.5 text-xs font-medium text-gray-300 transition-colors hover:bg-gray-700"
        >
          <Lightbulb size={13} /> Hint
        </button>
        <button
          onClick={() => ask('explain')}
          className="flex items-center justify-center gap-1.5 rounded-md border border-gray-800 bg-gray-800/60 py-1.5 text-xs font-medium text-gray-300 transition-colors hover:bg-gray-700"
        >
          <MessageSquareText size={13} /> Explain
        </button>
        <button
          onClick={() => ask('review')}
          disabled={!code.trim()}
          className="flex items-center justify-center gap-1.5 rounded-md border border-gray-800 bg-gray-800/60 py-1.5 text-xs font-medium text-gray-300 transition-colors hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ClipboardCheck size={13} /> Review
        </button>
      </div>

      {isLoading && <p className="text-xs text-gray-500">Thinking…</p>}
      {error && <p className="text-xs text-rose-400">{error}</p>}
      {result && !isLoading && (
        <div className="markdown-body max-w-none rounded-md border border-gray-800 bg-gray-950/60 p-3 text-xs leading-relaxed text-gray-300">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{result}</ReactMarkdown>
        </div>
      )}
    </div>
  );
};

export default AIPanel;
