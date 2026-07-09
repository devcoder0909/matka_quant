'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { executeCommand } from '@/lib/api';
import type { CommandResponse } from '@/lib/types';

const SUPPORTED_COMMANDS = [
  { cmd: 'import chart', desc: 'Import chart data from clipboard' },
  { cmd: 'analyze', desc: 'Run analysis for a market' },
  { cmd: 'status', desc: 'Show system status' },
  { cmd: 'markets', desc: 'List available markets' },
  { cmd: 'stats', desc: 'Show data statistics' },
  { cmd: 'frequency', desc: 'Show frequency analysis' },
  { cmd: 'help', desc: 'Show available commands' },
  { cmd: 'clear', desc: 'Clear terminal output' },
];

interface HistoryEntry {
  command: string;
  response: CommandResponse | null;
  error?: string;
  timestamp: Date;
}

export default function CommandInput() {
  const [input, setInput] = useState('');
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [isExecuting, setIsExecuting] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const outputRef = useRef<HTMLDivElement>(null);

  const filteredCommands = input.length > 0
    ? SUPPORTED_COMMANDS.filter((c) =>
        c.cmd.toLowerCase().startsWith(input.toLowerCase())
      )
    : SUPPORTED_COMMANDS;

  const handleExecute = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isExecuting) return;

    if (trimmed === 'clear') {
      setHistory([]);
      setInput('');
      return;
    }

    setIsExecuting(true);
    setShowSuggestions(false);

    const entry: HistoryEntry = {
      command: trimmed,
      response: null,
      timestamp: new Date(),
    };

    try {
      const response = await executeCommand(trimmed);
      entry.response = response;
    } catch (err) {
      entry.error = err instanceof Error ? err.message : 'Command failed';
    }

    setHistory((prev) => [...prev, entry]);
    setInput('');
    setHistoryIndex(-1);
    setIsExecuting(false);
  }, [input, isExecuting]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleExecute();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const pastCommands = history.map((h) => h.command);
      if (pastCommands.length > 0) {
        const newIndex = historyIndex < pastCommands.length - 1
          ? historyIndex + 1
          : historyIndex;
        setHistoryIndex(newIndex);
        setInput(pastCommands[pastCommands.length - 1 - newIndex]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1;
        setHistoryIndex(newIndex);
        const pastCommands = history.map((h) => h.command);
        setInput(pastCommands[pastCommands.length - 1 - newIndex]);
      } else {
        setHistoryIndex(-1);
        setInput('');
      }
    } else if (e.key === 'Tab') {
      e.preventDefault();
      if (filteredCommands.length === 1) {
        setInput(filteredCommands[0].cmd);
        setShowSuggestions(false);
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [history]);

  return (
    <div id="command-input" className="glass-card overflow-hidden">
      {/* Terminal Header */}
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-white/5 bg-black/20">
        <div className="flex gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80" />
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
        </div>
        <span className="text-[10px] font-mono text-gray-500 ml-2 tracking-wider">
          TRINETRA COMMAND INTERFACE
        </span>
      </div>

      {/* Terminal Output */}
      <div
        ref={outputRef}
        className="max-h-48 overflow-y-auto p-4 space-y-2 bg-black/30"
      >
        {history.length === 0 && (
          <p className="text-gray-600 text-xs font-mono">
            Type &apos;help&apos; to see available commands. Press Tab to autocomplete.
          </p>
        )}
        {history.map((entry, i) => (
          <div key={i} className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-emerald-400 font-mono text-xs font-semibold">
                TRINETRA &gt;
              </span>
              <span className="text-gray-300 font-mono text-xs">
                {entry.command}
              </span>
            </div>
            {entry.response && (
              <div
                className={`ml-4 text-xs font-mono ${
                  entry.response.success ? 'text-gray-400' : 'text-rose-400'
                }`}
              >
                {entry.response.message}
                {!!entry.response.data && (
                  <pre className="mt-1 text-gray-500 text-[10px] max-h-32 overflow-auto">
                    {JSON.stringify(entry.response.data, null, 2)}
                  </pre>
                )}
              </div>
            )}
            {entry.error && (
              <div className="ml-4 text-xs font-mono text-rose-400">
                ✗ {entry.error}
              </div>
            )}
          </div>
        ))}
        {isExecuting && (
          <div className="flex items-center gap-2 ml-4">
            <span className="inline-block w-2 h-4 bg-emerald-400 animate-pulse" />
            <span className="text-gray-500 text-xs font-mono">Processing...</span>
          </div>
        )}
      </div>

      {/* Input Line */}
      <div className="relative border-t border-white/5">
        <div className="flex items-center px-4 py-3 bg-black/20">
          <span className="text-emerald-400 font-mono text-xs font-semibold mr-2 flex-shrink-0">
            TRINETRA &gt;
          </span>
          <input
            ref={inputRef}
            id="command-line"
            type="text"
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            onKeyDown={handleKeyDown}
            placeholder="Enter command..."
            className="flex-1 bg-transparent text-gray-200 text-xs terminal-input outline-none placeholder:text-gray-700"
            autoComplete="off"
            spellCheck={false}
          />
        </div>

        {/* Autocomplete Suggestions */}
        {showSuggestions && filteredCommands.length > 0 && input.length > 0 && (
          <div className="absolute bottom-full left-0 right-0 bg-gray-900/95 backdrop-blur border border-gray-700/50 rounded-t-lg overflow-hidden z-20">
            {filteredCommands.map((cmd) => (
              <button
                key={cmd.cmd}
                onClick={() => {
                  setInput(cmd.cmd);
                  setShowSuggestions(false);
                  inputRef.current?.focus();
                }}
                className="w-full flex items-center justify-between px-4 py-2 hover:bg-cyan-500/10 transition-colors"
              >
                <span className="text-xs font-mono text-cyan-400">{cmd.cmd}</span>
                <span className="text-[10px] text-gray-500">{cmd.desc}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
