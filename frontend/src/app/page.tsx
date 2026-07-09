"use client";

import React, { useState, useEffect } from 'react';
import { runAnalysis } from '@/lib/api';

export default function Home() {
  const [predictions, setPredictions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        const today = new Date().toISOString().split('T')[0];
        const data = await runAnalysis("KALYAN", today);
        setPredictions(data?.summary?.quantum_predictions?.predictions?.top_jodis || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchPredictions();
  }, []);

  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-4">
      <h1 className="text-2xl font-mono text-zinc-500 mb-8 tracking-widest uppercase">Trinetra Prediction Output</h1>
      
      {loading ? (
        <div className="text-zinc-600 font-mono animate-pulse tracking-widest">CALCULATING...</div>
      ) : predictions.length === 0 ? (
        <div className="text-rose-500 font-mono">ERROR: INSUFFICIENT DATA</div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
          {predictions.map((p, i) => (
            <div 
              key={i} 
              className="flex flex-col items-center justify-center p-8 bg-zinc-900/50 rounded-xl border border-zinc-800 transition-all hover:bg-zinc-800/80 hover:border-zinc-600"
            >
              <div className="text-5xl font-black text-zinc-100 mb-2">{p.jodi}</div>
              <div className="text-xs font-mono text-cyan-500 tracking-widest">
                {(p.probability * 100).toFixed(1)}%
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
