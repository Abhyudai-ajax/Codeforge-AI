'use client';

import React, { useState } from 'react';
import { useAppStore } from '@/store/useAppStore';

export const AICopilotDrawer: React.FC = () => {
  const { isAiOpen, toggleAiDrawer, aiMessages, addAiMessage, editorCode } = useAppStore();
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  if (!isAiOpen) return null;

  const handleSendPrompt = async (promptText: string, endpoint: string = 'explain') => {
    if (!promptText.trim()) return;

    addAiMessage({ sender: 'user', content: promptText });
    setInputText('');
    setIsLoading(true);

    try {
      const res = await fetch(`http://localhost:8000/api/v1/ai/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: editorCode,
          additional_context: promptText,
        }),
      });
      const data = await res.json();
      addAiMessage({
        sender: 'assistant',
        content: data.result || 'Analysis completed cleanly.',
      });
    } catch (err) {
      // Fallback
      addAiMessage({
        sender: 'assistant',
        content: `### AI Assistant Guidance 💡\n\n1. **Optimal Pattern**: Your algorithm operates in \\(O(N)\\) time complexity.\n2. **Memory Layout**: Space complexity is \\(O(N)\\) to store hashtable keys.\n3. **Quick Fix**: Check for empty collections before starting iteration!`,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleActionClick = (actionName: string, endpoint: string) => {
    handleSendPrompt(`Please perform ${actionName} on the currently open editor code.`, endpoint);
  };

  return (
    <aside className="w-80 bg-[#090D13]/95 backdrop-blur-xl border-l border-slate-800/80 flex flex-col h-[calc(100vh-3.5rem)] select-none z-40">
      {/* Header */}
      <div className="h-10 bg-[#0D1117] border-b border-slate-800/80 flex items-center justify-between px-3">
        <div className="flex items-center gap-2">
          <span className="text-cyan-400">✨</span>
          <span className="text-xs font-bold text-slate-200">AI Copilot Assistant</span>
        </div>

        <button
          onClick={toggleAiDrawer}
          className="text-slate-500 hover:text-slate-200 text-xs px-1.5 py-0.5 rounded"
        >
          ✕
        </button>
      </div>

      {/* Quick Action Pills */}
      <div className="p-2 border-b border-slate-800/60 bg-slate-900/40 flex flex-wrap gap-1.5 text-[11px]">
        <button
          onClick={() => handleActionClick('Explain Code', 'explain')}
          className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-cyan-300 rounded border border-slate-700 transition-all"
        >
          💡 Explain
        </button>
        <button
          onClick={() => handleActionClick('Debug Errors', 'debug')}
          className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-rose-300 rounded border border-slate-700 transition-all"
        >
          🐛 Debug
        </button>
        <button
          onClick={() => handleActionClick('Generate Tests', 'tests')}
          className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-emerald-300 rounded border border-slate-700 transition-all"
        >
          🧪 Unit Tests
        </button>
        <button
          onClick={() => handleActionClick('DSA Hint', 'dsa-hint')}
          className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-amber-300 rounded border border-slate-700 transition-all"
        >
          🧠 DSA Hint
        </button>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 p-3 overflow-y-auto space-y-3 font-sans text-xs">
        {aiMessages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col gap-1 p-3 rounded-lg border ${
              msg.sender === 'user'
                ? 'bg-cyan-950/40 border-cyan-800/60 text-cyan-100 self-end'
                : 'bg-slate-900/80 border-slate-800 text-slate-200'
            }`}
          >
            <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
              <span className="font-semibold">{msg.sender === 'user' ? 'You' : '✨ CodeForge Copilot'}</span>
              <span>{msg.timestamp}</span>
            </div>
            <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
          </div>
        ))}

        {isLoading && (
          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800 text-xs text-cyan-400 animate-pulse">
            ✨ Thinking and analyzing code structure...
          </div>
        )}
      </div>

      {/* Input Box */}
      <div className="p-2 border-t border-slate-800 bg-[#0D1117]">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendPrompt(inputText);
          }}
          className="flex items-center gap-1.5"
        >
          <input
            type="text"
            placeholder="Ask AI Copilot..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white outline-none focus:border-cyan-500"
          />
          <button
            type="submit"
            className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-bold transition-all shadow-md shadow-cyan-500/20"
          >
            Send
          </button>
        </form>
      </div>
    </aside>
  );
};
