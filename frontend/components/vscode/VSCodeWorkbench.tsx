'use client';

import React, { useState } from 'react';
import { useAppStore } from '@/store/useAppStore';

export const VSCodeWorkbench: React.FC = () => {
  const {
    files,
    activeFileId,
    openFileIds,
    setActiveFile,
    closeFileTab,
    editorCode,
    setEditorCode,
    updateFileContent,
    createFile,
    deleteFile,
    selectedLanguage,
    setSelectedLanguage,
    terminalOutput,
    clearTerminalOutput,
  } = useAppStore();

  const [sidebarTab, setSidebarTab] = useState<'explorer' | 'search' | 'git'>('explorer');
  const [newFileName, setNewFileName] = useState('');
  const [isCreatingFile, setIsCreatingFile] = useState(false);
  const [terminalTab, setTerminalTab] = useState<'output' | 'terminal'>('terminal');

  const activeFile = files.find((f) => f.id === activeFileId);

  const handleCreateFileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newFileName.trim()) {
      createFile(newFileName.trim(), newFileName.trim());
      setNewFileName('');
      setIsCreatingFile(false);
    }
  };

  const handleCodeChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setEditorCode(val);
    if (activeFileId) {
      updateFileContent(activeFileId, val);
    }
  };

  // Line count computation for line numbers column
  const lineCount = editorCode.split('\n').length;
  const lineNumbers = Array.from({ length: lineCount }, (_, i) => i + 1);

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-3.5rem)] bg-[#0D1117] text-slate-300 font-sans overflow-hidden">
      {/* Main Workspace Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* 1. Activity Bar (Far Left 48px) */}
        <div className="w-12 bg-[#090D13] border-r border-slate-800/80 flex flex-col items-center py-3 justify-between select-none">
          <div className="flex flex-col gap-4 text-slate-500">
            <button
              onClick={() => setSidebarTab('explorer')}
              className={`p-2 rounded-lg transition-all ${
                sidebarTab === 'explorer'
                  ? 'text-cyan-400 bg-slate-800/80 shadow-md shadow-cyan-500/10'
                  : 'hover:text-slate-200'
              }`}
              title="File Explorer (Ctrl+Shift+E)"
            >
              📁
            </button>
            <button
              onClick={() => setSidebarTab('search')}
              className={`p-2 rounded-lg transition-all ${
                sidebarTab === 'search'
                  ? 'text-cyan-400 bg-slate-800/80 shadow-md shadow-cyan-500/10'
                  : 'hover:text-slate-200'
              }`}
              title="Global Search"
            >
              🔍
            </button>
            <button
              onClick={() => setSidebarTab('git')}
              className={`p-2 rounded-lg transition-all ${
                sidebarTab === 'git'
                  ? 'text-cyan-400 bg-slate-800/80 shadow-md shadow-cyan-500/10'
                  : 'hover:text-slate-200'
              }`}
              title="Source Control (Git)"
            >
              🔀
            </button>
          </div>

          <div className="flex flex-col gap-3 text-slate-500">
            <button className="hover:text-slate-200 p-2" title="Settings">⚙️</button>
          </div>
        </div>

        {/* 2. Sidebar Pane (220px) */}
        <div className="w-56 bg-[#0D1117] border-r border-slate-800/80 flex flex-col select-none">
          <div className="h-9 px-3 border-b border-slate-800/80 flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-400">
            <span>{sidebarTab === 'explorer' ? 'Explorer: Workspace' : sidebarTab === 'search' ? 'Search Files' : 'Source Control'}</span>
            {sidebarTab === 'explorer' && (
              <button
                onClick={() => setIsCreatingFile(!isCreatingFile)}
                className="text-slate-400 hover:text-cyan-400 p-1 text-sm font-bold"
                title="New File"
              >
                +
              </button>
            )}
          </div>

          {/* Sidebar Content */}
          <div className="flex-1 p-2 overflow-y-auto">
            {sidebarTab === 'explorer' && (
              <div>
                <div className="text-[11px] font-semibold text-slate-500 uppercase px-2 mb-1">PROJECT FILES</div>

                {isCreatingFile && (
                  <form onSubmit={handleCreateFileSubmit} className="px-2 mb-2">
                    <input
                      type="text"
                      autoFocus
                      placeholder="filename.py"
                      value={newFileName}
                      onChange={(e) => setNewFileName(e.target.value)}
                      className="w-full bg-slate-900 border border-cyan-500 rounded px-2 py-1 text-xs text-white outline-none"
                    />
                  </form>
                )}

                <div className="space-y-0.5">
                  {files.map((file) => {
                    const isActive = file.id === activeFileId;
                    return (
                      <div
                        key={file.id}
                        onClick={() => setActiveFile(file.id)}
                        className={`group flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs cursor-pointer transition-all ${
                          isActive
                            ? 'bg-cyan-950/60 text-cyan-300 font-medium border-l-2 border-cyan-400'
                            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                        }`}
                      >
                        <div className="flex items-center gap-2 truncate">
                          <span>{file.name.endsWith('.py') ? '🐍' : file.name.endsWith('.js') ? '📜' : '📄'}</span>
                          <span className="truncate">{file.name}</span>
                        </div>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteFile(file.id);
                          }}
                          className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-rose-400 text-xs px-1"
                        >
                          ✕
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {sidebarTab === 'git' && (
              <div className="p-2 text-xs text-slate-400 space-y-3">
                <div className="flex items-center justify-between bg-slate-900 p-2 rounded border border-slate-800">
                  <span>Branch: <strong className="text-cyan-400">main</strong></span>
                  <span className="text-[10px] bg-emerald-950 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-800">Clean</span>
                </div>
                <div className="text-[11px] text-slate-500">2 staged changes ready for PR</div>
              </div>
            )}
          </div>
        </div>

        {/* 3. Central Editor & Workspace Area */}
        <div className="flex-1 flex flex-col bg-[#0D1117] overflow-hidden">
          {/* File Tabs Bar */}
          <div className="h-9 bg-[#090D13] border-b border-slate-800/80 flex items-center px-1 overflow-x-auto select-none">
            {openFileIds.map((id) => {
              const file = files.find((f) => f.id === id);
              if (!file) return null;
              const isActive = id === activeFileId;

              return (
                <div
                  key={id}
                  onClick={() => setActiveFile(id)}
                  className={`flex items-center gap-2 px-3 py-1.5 text-xs border-r border-slate-800/60 cursor-pointer transition-all ${
                    isActive
                      ? 'bg-[#0D1117] text-cyan-300 font-semibold border-t-2 border-t-cyan-400'
                      : 'text-slate-500 hover:text-slate-300 hover:bg-slate-900/40'
                  }`}
                >
                  <span>{file.name.endsWith('.py') ? '🐍' : '📜'}</span>
                  <span>{file.name}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      closeFileTab(id);
                    }}
                    className="hover:text-rose-400 ml-1 text-[10px]"
                  >
                    ✕
                  </button>
                </div>
              );
            })}
          </div>

          {/* Editor Header Bar / Breadcrumbs */}
          <div className="h-7 bg-[#0D1117] border-b border-slate-800/50 flex items-center justify-between px-4 text-xs text-slate-400 select-none">
            <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
              <span>project</span>
              <span>›</span>
              <span className="text-cyan-300 font-mono">{activeFile?.path || 'main.py'}</span>
            </div>

            <div className="flex items-center gap-3">
              {/* Language Switcher */}
              <select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                className="bg-slate-900 border border-slate-800 text-cyan-300 text-[11px] rounded px-2 py-0.5 outline-none font-mono"
              >
                <option value="python">Python 3.11</option>
                <option value="javascript">JavaScript ES6</option>
              </select>
            </div>
          </div>

          {/* Main Code Editor Input Area */}
          <div className="flex-1 flex overflow-hidden font-mono text-sm leading-6">
            {/* Line Numbers Column */}
            <div className="w-12 bg-[#090D13]/60 text-slate-600 text-right pr-3 py-3 select-none border-r border-slate-800/40 font-mono text-xs">
              {lineNumbers.map((n) => (
                <div key={n}>{n}</div>
              ))}
            </div>

            {/* Editable Code TextArea */}
            <div className="flex-1 relative bg-[#0D1117] p-3 overflow-auto">
              <textarea
                value={editorCode}
                onChange={handleCodeChange}
                spellCheck={false}
                className="w-full h-full bg-transparent text-slate-100 font-mono text-xs leading-6 outline-none resize-none code-editor-area"
              />
            </div>
          </div>

          {/* Integrated Terminal & Output Drawer */}
          <div className="h-44 bg-[#090D13] border-t border-slate-800 flex flex-col font-mono">
            {/* Terminal Header */}
            <div className="h-7 bg-[#0D1117] border-b border-slate-800/60 flex items-center justify-between px-3 text-xs select-none">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setTerminalTab('terminal')}
                  className={`font-semibold transition-all ${
                    terminalTab === 'terminal' ? 'text-cyan-400 border-b-2 border-cyan-400 pb-0.5' : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  Terminal
                </button>
                <button
                  onClick={() => setTerminalTab('output')}
                  className={`font-semibold transition-all ${
                    terminalTab === 'output' ? 'text-cyan-400 border-b-2 border-cyan-400 pb-0.5' : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  Output Console
                </button>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={clearTerminalOutput}
                  className="text-slate-500 hover:text-slate-300 text-[11px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800"
                >
                  Clear
                </button>
              </div>
            </div>

            {/* Terminal Output Stream */}
            <div className="flex-1 p-3 overflow-y-auto text-xs text-slate-300 space-y-1">
              {terminalOutput.split('\n').map((line, idx) => (
                <div key={idx} className={line.includes('PASSED') ? 'text-emerald-400 font-semibold' : line.includes('Error') ? 'text-rose-400 font-semibold' : ''}>
                  {line}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 4. VSCode Bottom Status Bar */}
      <footer className="h-6 bg-slate-950 border-t border-slate-800/80 flex items-center justify-between px-3 text-[11px] text-slate-400 select-none">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1 text-cyan-400 font-mono">
            <span>🔀</span> main
          </span>
          <span className="text-slate-500">|</span>
          <span className="text-slate-400">Errors: <strong className="text-emerald-400">0</strong></span>
        </div>

        <div className="flex items-center gap-4 font-mono text-[10px]">
          <span>Ln 1, Col 1</span>
          <span>UTF-8</span>
          <span className="text-cyan-400 font-semibold uppercase">{selectedLanguage}</span>
          <span className="flex items-center gap-1 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Copilot Ready
          </span>
        </div>
      </footer>
    </div>
  );
};
