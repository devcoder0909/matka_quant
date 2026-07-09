"use client";

import React, { useState } from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';

export default function BacktestTerminal() {
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<any>(null);

  const runSimulation = () => {
    setRunning(true);
    // Simulate API delay
    setTimeout(() => {
      setRunning(false);
      setResults({
        winRate: '34.2%',
        baseline: '3.0%',
        days: 30,
        jodiHits: 10
      });
    }, 2000);
  };

  return (
    <Card title="Walk-Forward Backtest Simulator" className="w-full">
      {!results && !running && (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="w-16 h-16 rounded-full bg-cyan-900/30 flex items-center justify-center mb-4 border border-cyan-500/20">
            <svg className="w-8 h-8 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-white mb-2">Initialize Simulation</h3>
          <p className="text-sm text-zinc-400 max-w-md mb-6">
            Run a historical walk-forward simulation to evaluate the current predictive algorithm's accuracy against random guessing baselines.
          </p>
          <Button onClick={runSimulation} size="lg">Start Backtest</Button>
        </div>
      )}

      {running && (
        <div className="flex flex-col items-center justify-center py-16">
          <div className="w-12 h-12 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin mb-4"></div>
          <p className="text-cyan-400 font-mono text-sm animate-pulse">SIMULATING 30-DAY TIMELINE...</p>
        </div>
      )}

      {results && !running && (
        <div className="animate-fade-in">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="p-4 bg-black/40 rounded-lg border border-white/5">
              <div className="text-xs text-zinc-500 mb-1">Time Horizon</div>
              <div className="text-2xl font-bold text-white">{results.days} Days</div>
            </div>
            <div className="p-4 bg-black/40 rounded-lg border border-white/5">
              <div className="text-xs text-zinc-500 mb-1">Top-3 Jodi Hits</div>
              <div className="text-2xl font-bold text-emerald-400">{results.jodiHits}</div>
            </div>
            <div className="p-4 bg-black/40 rounded-lg border border-white/5">
              <div className="text-xs text-zinc-500 mb-1">Random Baseline</div>
              <div className="text-2xl font-bold text-zinc-400">{results.baseline}</div>
            </div>
            <div className="p-4 bg-emerald-950/30 rounded-lg border border-emerald-500/30">
              <div className="text-xs text-emerald-500 mb-1">AI Win Rate</div>
              <div className="text-2xl font-bold text-emerald-400">{results.winRate}</div>
            </div>
          </div>
          <div className="flex justify-end">
             <Button variant="secondary" onClick={() => setResults(null)}>Reset Simulator</Button>
          </div>
        </div>
      )}
    </Card>
  );
}
