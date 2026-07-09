"use client";

import React, { useState, useEffect } from 'react';
import { runAnalysis } from '@/lib/api';
import ChartInput from '../components/input/ChartInput';

export default function Home() {
  const [predictions, setPredictions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchPredictions = async () => {
    setLoading(true);
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

  useEffect(() => {
    fetchPredictions();
  }, [refreshKey]); // Refetches when refreshKey changes

  // Expose a way to refresh predictions after importing
  const handleImportSuccess = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="min-h-screen bg-black text-white p-4 md:p-8 space-y-12 max-w-5xl mx-auto">
      
      {/* Import Section */}
      <div className="w-full">
        <h2 className="text-xl font-mono text-zinc-500 mb-4 tracking-widest uppercase text-center">Data Gateway</h2>
        <ChartInput />
      </div>

      {/* Prediction Section */}
      <div className="w-full flex flex-col items-center border-t border-zinc-900 pt-12">
        <div className="flex flex-col items-center justify-center mb-8 gap-4">
          <h1 className="text-2xl font-mono text-zinc-500 tracking-widest uppercase">Trinetra Prediction Output</h1>
          <button 
            onClick={() => setRefreshKey(prev => prev + 1)}
            className="px-4 py-2 border border-cyan-500/50 rounded text-cyan-400 font-mono text-xs hover:bg-cyan-500/10 transition-colors"
          >
            REFRESH PREDICTIONS
          </button>
        </div>
        
        {loading ? (
          <div className="text-zinc-600 font-mono animate-pulse tracking-widest">CALCULATING...</div>
        ) : predictions.length === 0 ? (
          <div className="text-rose-500 font-mono">ERROR: INSUFFICIENT DATA. PLEASE IMPORT CHART ABOVE.</div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-6 w-full">
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

    </div>
  );
}
