'use client';

import React from 'react';

export const UserProfileView: React.FC = () => {
  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-3.5rem)] bg-[#0B0F17] text-slate-200 overflow-y-auto p-6 font-sans">
      <div className="max-w-5xl mx-auto w-full space-y-6">
        {/* Profile Banner Card */}
        <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-6 flex flex-col md:flex-row items-center justify-between gap-6 shadow-xl">
          <div className="flex items-center gap-5">
            <div className="w-20 h-20 rounded-full bg-gradient-to-tr from-cyan-400 via-blue-500 to-purple-600 flex items-center justify-center text-2xl font-bold text-white shadow-lg shadow-cyan-500/20 border-2 border-cyan-300">
              AR
            </div>
            <div className="space-y-1">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                Alex Rivera
                <span className="text-xs bg-cyan-950 text-cyan-400 border border-cyan-800 px-2 py-0.5 rounded-full font-mono">
                  PRO MEMBER
                </span>
              </h2>
              <p className="text-xs text-cyan-400 font-mono">FAANG Senior Software Engineer | Distributed Systems & Algorithms</p>
              <div className="flex items-center gap-4 text-xs text-slate-400 pt-1">
                <span>📧 alex@codeforge.ai</span>
                <span>•</span>
                <span>🐙 @alexrivera-faang</span>
                <span>•</span>
                <span>📍 San Francisco, CA</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4 border-t md:border-t-0 md:border-l border-slate-800 pt-4 md:pt-0 md:pl-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-white font-mono">#1,420</div>
              <div className="text-[11px] text-slate-400 uppercase">Global Rank</div>
            </div>
            <div className="text-center pl-4 border-l border-slate-800">
              <div className="text-2xl font-bold text-emerald-400 font-mono">1,840</div>
              <div className="text-[11px] text-slate-400 uppercase">Contest Rating</div>
            </div>
          </div>
        </div>

        {/* Analytics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Solved Problems Breakdown */}
          <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-5 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">DSA Solved Breakdown</h3>

            <div className="flex items-center justify-between">
              <div className="relative w-24 h-24 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-xl font-bold text-white font-mono">4</div>
                  <div className="text-[10px] text-slate-400">/ 5 Solved</div>
                </div>
              </div>

              <div className="flex-1 space-y-2 pl-4">
                <div>
                  <div className="flex justify-between text-xs font-mono mb-1">
                    <span className="text-emerald-400">Easy</span>
                    <span>3 / 3</span>
                  </div>
                  <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-400 w-full"></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-mono mb-1">
                    <span className="text-amber-400">Medium</span>
                    <span>1 / 2</span>
                  </div>
                  <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-amber-400 w-1/2"></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-mono mb-1">
                    <span className="text-rose-400">Hard</span>
                    <span>0 / 1</span>
                  </div>
                  <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-rose-400 w-0"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Skill Badges */}
          <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-5 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Top Badges & Skills</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center gap-2">
                <span className="text-lg">🏆</span>
                <div>
                  <div className="font-bold text-white text-xs">50 Days Badge</div>
                  <div className="text-[10px] text-slate-500">2026 Streak</div>
                </div>
              </div>

              <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center gap-2">
                <span className="text-lg">⚡</span>
                <div>
                  <div className="font-bold text-white text-xs">Fastest Runtime</div>
                  <div className="text-[10px] text-slate-500">Top 1% Ms</div>
                </div>
              </div>
            </div>
          </div>

          {/* Card 3: GitHub Activity Heatmap */}
          <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-5 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">52-Week Submission Heatmap</h3>
            <div className="grid grid-cols-12 gap-1.5 pt-2">
              {Array.from({ length: 48 }, (_, i) => (
                <div
                  key={i}
                  className={`w-3.5 h-3.5 rounded-sm ${
                    i % 7 === 0
                      ? 'bg-emerald-500 shadow-sm shadow-emerald-500/50'
                      : i % 3 === 0
                      ? 'bg-emerald-700'
                      : i % 2 === 0
                      ? 'bg-emerald-900'
                      : 'bg-slate-800'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
