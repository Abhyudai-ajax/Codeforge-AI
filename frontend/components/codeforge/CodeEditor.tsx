'use client';

import React from 'react';
import Editor from '@monaco-editor/react';
import { ChevronDown } from 'lucide-react';
import { useLanguages } from '@/lib/api/hooks';
import type { LanguageResponse } from '@/lib/api/types';

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language: string;
  onLanguageChange: (language: string) => void;
  availableLanguages?: string[];
  fileName?: string;
  height?: string | number;
}

/** Maps our canonical language ids to the ids Monaco's built-in grammars expect. */
function toMonacoLanguage(languages: LanguageResponse[] | undefined, id: string): string {
  return languages?.find((l) => l.id === id)?.monaco_id ?? id;
}

const CodeEditor: React.FC<CodeEditorProps> = ({
  value,
  onChange,
  language,
  onLanguageChange,
  availableLanguages,
  fileName,
  height = '420px',
}) => {
  const { data: languages } = useLanguages();
  const selectable =
    languages?.filter((l) => !availableLanguages || availableLanguages.includes(l.id)) ?? [];

  return (
    <div className="flex flex-1 flex-col overflow-hidden rounded-lg border border-gray-800 bg-[#0D1117]">
      <div className="flex items-center gap-2 border-b border-gray-800 bg-gray-900/80 px-4 py-2.5">
        <span className="text-sm font-medium text-gray-300">
          {fileName ?? `solution${extensionFor(languages, language)}`}
        </span>
        <div className="relative ml-auto">
          <select
            value={language}
            onChange={(e) => onLanguageChange(e.target.value)}
            className="appearance-none rounded-md border border-gray-700 bg-gray-800 py-1 pl-3 pr-7 text-xs font-medium text-gray-200 focus:border-cyan-600 focus:outline-none"
          >
            {selectable.map((l) => (
              <option key={l.id} value={l.id}>
                {l.label}
              </option>
            ))}
          </select>
          <ChevronDown
            size={12}
            className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-gray-500"
          />
        </div>
      </div>
      <div className="flex-1" style={{ minHeight: height }}>
        <Editor
          height={height}
          theme="vs-dark"
          language={toMonacoLanguage(languages, language)}
          value={value}
          onChange={(v) => onChange(v ?? '')}
          options={{
            fontSize: 13,
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            padding: { top: 14 },
            automaticLayout: true,
            tabSize: 4,
          }}
        />
      </div>
    </div>
  );
};

function extensionFor(languages: LanguageResponse[] | undefined, id: string): string {
  return languages?.find((l) => l.id === id)?.file_extension ?? '';
}

export default CodeEditor;
