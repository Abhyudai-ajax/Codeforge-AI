'use client';

import React, { useState } from 'react';

export const GitHubPRReview: React.FC = () => {
  const [isAiReviewing, setIsAiReviewing] = useState(false);
  const [aiReviewResult, setAiReviewResult] = useState<any>({
    summary: '✅ Excellent implementation! The O(1) doubly-linked list node reconnection prevents hashtable traversal overhead.',
    code_quality_score: 94,
    security_risk: 'Low Risk',
    suggestions: [
      { file: 'backend/app/dsa/lru_cache.py', line: 14, type: 'performance', comment: 'Consider using __slots__ on Node class for optimal memory layout.' },
      { file: 'tests/test_lru_cache.py', line: 6, type: 'coverage', comment: 'Add edge case assertion when capacity is 1.' },
    ],
  });

  const triggerAiReview = async () => {
    setIsAiReviewing(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/github/pulls/pr-101/ai-review', {
        method: 'POST',
      });
      const data = await res.json();
      setAiReviewResult(data);
    } catch (err) {
      // Fallback
    } finally {
      setIsAiReviewing(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-3.5rem)] bg-[#0B0F17] text-slate-200 overflow-hidden font-sans">
      {/* GitHub PR Header */}
      <div className="bg-slate-900/90 border-b border-slate-800 p-4 flex flex-col gap-3 select-none">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-purple-400 font-bold text-sm">🔀 GitHub Pull Request #101</span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-950 text-purple-300 border border-purple-800">
              Open
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={triggerAiReview}
              disabled={isAiReviewing}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-md shadow-purple-500/20 transition-all active:scale-95 disabled:opacity-50"
            >
              <span>✨</span>
              <span>{isAiReviewing ? 'Auditing Code...' : 'Trigger AI Code Audit'}</span>
            </button>
          </div>
        </div>

        <div>
          <h2 className="text-lg font-bold text-white">
            feat(dsa): Optimized LRU Cache using Doubly Linked List & Hash Map
          </h2>
          <div className="flex items-center gap-3 text-xs text-slate-400 mt-1 font-mono">
            <span>Author: <strong className="text-cyan-400">codeforge-dev</strong></span>
            <span>•</span>
            <span>Branch: <span className="bg-slate-800 px-1.5 py-0.5 rounded text-purple-300">feature/lru-cache-opt</span> → <span className="bg-slate-800 px-1.5 py-0.5 rounded text-cyan-300">main</span></span>
          </div>
        </div>
      </div>

      {/* Main Diff & Review Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Column: File Diffs (65% width) */}
        <div className="w-[65%] border-r border-slate-800 flex flex-col bg-[#0D1117] overflow-y-auto p-4 space-y-4 font-mono text-xs">
          <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-2">
            <span>Showing 2 changed files with 46 additions and 12 deletions</span>
            <span className="text-emerald-400">+46</span> <span className="text-rose-400">-12</span>
          </div>

          {/* File Diff Card 1 */}
          <div className="bg-slate-900/90 rounded-lg border border-slate-800 overflow-hidden">
            <div className="h-8 bg-slate-950 px-3 flex items-center justify-between text-xs font-bold text-slate-300 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span>🐍</span>
                <span>backend/app/dsa/lru_cache.py</span>
              </div>
              <span className="text-[10px] text-emerald-400 bg-emerald-950 px-1.5 py-0.5 rounded">Modified</span>
            </div>

            <div className="p-2 space-y-0.5 font-mono text-[11px] leading-5">
              <div className="bg-slate-950/60 text-slate-500 px-2 py-0.5">@@ -1,12 +1,28 @@</div>
              <div className="text-slate-400 px-2"> class LRUCache:</div>
              <div className="text-slate-400 px-2">     def __init__(self, capacity: int):</div>
              <div className="text-slate-400 px-2">         self.capacity = capacity</div>
              <div className="bg-rose-950/50 text-rose-300 px-2">-        self.cache = {}</div>
              <div className="bg-emerald-950/60 text-emerald-300 px-2">+        self.cache = {}  # key -&gt; Node</div>
              <div className="bg-emerald-950/60 text-emerald-300 px-2">+        self.head = Node(0, 0)</div>
              <div className="bg-emerald-950/60 text-emerald-300 px-2">+        self.tail = Node(0, 0)</div>
              <div className="bg-emerald-950/60 text-emerald-300 px-2">+        self.head.next = self.tail</div>
              <div className="bg-emerald-950/60 text-emerald-300 px-2">+        self.tail.prev = self.head</div>
              <div className="text-slate-400 px-2">     def get(self, key: int) -&gt; int:</div>
              <div className="text-slate-400 px-2">         if key in self.cache:</div>
              <div className="bg-emerald-950/60 text-emerald-300 px-2">+            node = self.cache[key]</div>
              <div className="bg-emerald-950/60 text-emerald-300 px-2">+            self._remove(node)</div>
              <div className="bg-emerald-950/60 text-emerald-300 px-2">+            self._add(node)</div>
              <div className="bg-emerald-950/60 text-emerald-300 px-2">+            return node.val</div>
              <div className="bg-rose-950/50 text-rose-300 px-2">-            val = self.cache.pop(key)</div>
              <div className="text-slate-400 px-2">         return -1</div>
            </div>
          </div>

          {/* File Diff Card 2 */}
          <div className="bg-slate-900/90 rounded-lg border border-slate-800 overflow-hidden">
            <div className="h-8 bg-slate-950 px-3 flex items-center justify-between text-xs font-bold text-slate-300 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span>🧪</span>
                <span>tests/test_lru_cache.py</span>
              </div>
              <span className="text-[10px] text-emerald-400 bg-emerald-950 px-1.5 py-0.5 rounded">Added</span>
            </div>

            <div className="p-2 space-y-0.5 font-mono text-[11px] leading-5">
              <div className="bg-emerald-950/60 text-emerald-300 px-2">+def test_lru_cache_operations():</div>
              <div className="bg-emerald-950/60 text-emerald-300 px-2">+    cache = LRUCache(2)</div>
              <div className="bg-emerald-950/60 text-emerald-300 px-2">+    cache.put(1, 1)</div>
              <div className="bg-emerald-950/60 text-emerald-300 px-2">+    cache.put(2, 2)</div>
              <div className="bg-emerald-950/60 text-emerald-300 px-2">+    assert cache.get(1) == 1</div>
            </div>
          </div>
        </div>

        {/* Right Column: AI Code Review Summary Drawer (35% width) */}
        <div className="w-[35%] bg-[#090D13] p-4 flex flex-col gap-4 overflow-y-auto">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">AI Automated PR Review</h3>
            <span className="text-xs font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800">
              Score: {aiReviewResult.code_quality_score}/100
            </span>
          </div>

          {/* AI Summary Box */}
          <div className="bg-slate-900/90 p-3 rounded-lg border border-slate-800 text-xs leading-relaxed space-y-2">
            <div className="text-cyan-400 font-bold">Audit Executive Summary</div>
            <p className="text-slate-300">{aiReviewResult.summary}</p>
          </div>

          {/* Security & Risk Badge */}
          <div className="bg-slate-900 p-3 rounded-lg border border-slate-800 flex items-center justify-between text-xs">
            <span className="text-slate-400">Security Vulnerabilities:</span>
            <span className="text-emerald-400 font-bold font-mono">{aiReviewResult.security_risk}</span>
          </div>

          {/* Suggestions list */}
          <div className="space-y-2">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Inline Recommendations</div>
            {aiReviewResult.suggestions?.map((s: any, idx: number) => (
              <div key={idx} className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-xs space-y-1">
                <div className="flex items-center justify-between text-[11px] font-mono text-cyan-300">
                  <span>{s.file}:{s.line}</span>
                  <span className="uppercase text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-amber-400">{s.type}</span>
                </div>
                <p className="text-slate-300 text-[11px] leading-relaxed">{s.comment}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
