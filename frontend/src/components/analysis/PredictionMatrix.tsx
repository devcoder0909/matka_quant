"use client";

import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import { runAnalysis } from '@/lib/api';

interface PredictionMatrixProps {
  marketCode?: string;
}

export default function PredictionMatrix({ marketCode = 'KALYAN' }: PredictionMatrixProps) {
  const [activeTab, setActiveTab] = useState<'jodi' | 'ank'>('jodi');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [predictionData, setPredictionData] = useState<any>(null);

  const fetchPredictions = async () => {
    if (!marketCode) return;
    setLoading(true);
    setError(null);
    try {
      const today = new Date().toISOString().split('T')[0];
      const data = await runAnalysis(marketCode, today);
      setPredictionData(data?.summary?.quantum_predictions || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch predictions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPredictions();
  }, [marketCode]);

  // Extract values safely
  const topJodi = predictionData?.predictions?.top_jodis?.[0];
  const topAnk = predictionData?.predictions?.top_anks?.[0];
  
  const displayValue = activeTab === 'jodi' ? (topJodi?.jodi || '--') : (topAnk?.ank || '-');
  const confidenceScore = activeTab === 'jodi' 
    ? (topJodi?.confidence ? (topJodi.confidence * 100).toFixed(1) + '%' : '--%')
    : (topAnk?.confidence ? (topAnk.confidence * 100).toFixed(1) + '%' : '--%');
    
  // Time-decay factor
  const jodiTimeScore = topJodi?.signals?.time_decay_score || 0;
  const timeDecayBadge = jodiTimeScore > 0.8 ? 'success' : (jodiTimeScore > 0.4 ? 'warning' : 'danger');
  const timeDecayLabel = jodiTimeScore > 0.8 ? 'High' : (jodiTimeScore > 0.4 ? 'Moderate' : 'Low');

  // Markov match factor
  const jodiMarkovScore = topJodi?.signals?.transition_score || 0;
  const markovBadge = jodiMarkovScore > 0.7 ? 'success' : (jodiMarkovScore > 0.3 ? 'warning' : 'danger');
  const markovLabel = jodiMarkovScore > 0.7 ? 'Strong Match' : (jodiMarkovScore > 0.3 ? 'Moderate' : 'Weak');

  return (
    <Card title={`Quantum Prediction Matrix — ${marketCode}`} glow className="w-full h-full min-h-[400px]">
      <div className="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
        <div className="flex gap-2">
          <Button 
            variant={activeTab === 'jodi' ? 'primary' : 'secondary'} 
            size="sm" 
            onClick={() => setActiveTab('jodi')}
          >
            Jodi Probabilities
          </Button>
          <Button 
            variant={activeTab === 'ank' ? 'primary' : 'secondary'} 
            size="sm" 
            onClick={() => setActiveTab('ank')}
          >
            Ank Probabilities
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={fetchPredictions} loading={loading}>
            Refresh
          </Button>
          <Badge variant="success" pulse>LIVE</Badge>
        </div>
      </div>

      {loading && !predictionData ? (
        <div className="flex flex-col items-center justify-center py-20 opacity-50">
           <div className="w-12 h-12 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin mb-4"></div>
           <p className="text-cyan-400 font-mono text-sm animate-pulse">CALCULATING PROBABILITIES...</p>
        </div>
      ) : error ? (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400">
          <p className="font-bold mb-1">Inference Engine Error</p>
          <p className="text-sm">{error}</p>
        </div>
      ) : !predictionData ? (
        <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg text-amber-400 text-center py-10">
          <p className="font-bold mb-1">Insufficient Data</p>
          <p className="text-sm">Please import historical chart data for {marketCode} first.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-fade-in">
          {/* Top Prediction */}
          <div className="flex flex-col items-center justify-center p-8 border border-cyan-500/30 rounded-xl bg-cyan-950/20 shadow-[0_0_30px_rgba(34,211,238,0.1)] relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-400 to-emerald-400"></div>
            <span className="text-zinc-400 text-sm tracking-widest uppercase mb-2">Highest Probability</span>
            <span className="text-8xl font-black text-transparent bg-clip-text bg-gradient-to-br from-white to-cyan-400">
              {displayValue}
            </span>
            
            <div className="mt-6 flex flex-col w-full gap-2">
              <div className="flex justify-between text-sm">
                <span className="text-zinc-500">Confidence Score</span>
                <span className="text-cyan-400 font-mono">{confidenceScore}</span>
              </div>
              <div className="w-full bg-black/50 h-2 rounded-full overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-cyan-500 to-emerald-400 h-full transition-all duration-1000" 
                  style={{ width: confidenceScore !== '--%' ? confidenceScore : '0%' }}
                ></div>
              </div>
            </div>
          </div>

          {/* Transition Factors */}
          <div className="flex flex-col gap-4">
            <h4 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider">Markov Transition Factors</h4>
            
            <div className="p-3 rounded-lg bg-black/40 border border-white/5 flex justify-between items-center">
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded bg-zinc-800 flex items-center justify-center font-mono text-xs">T-1</span>
                <span className="text-sm text-zinc-400">Time-Decay Momentum</span>
              </div>
              <Badge variant={timeDecayBadge as any}>{timeDecayLabel}</Badge>
            </div>

            <div className="p-3 rounded-lg bg-black/40 border border-white/5 flex justify-between items-center">
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded bg-zinc-800 flex items-center justify-center font-mono text-xs">M-C</span>
                <span className="text-sm text-zinc-400">Markov Chain Match</span>
              </div>
              <Badge variant={markovBadge as any}>{markovLabel}</Badge>
            </div>
            
            <div className="p-3 rounded-lg bg-black/40 border border-white/5 flex justify-between items-center">
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded bg-zinc-800 flex items-center justify-center font-mono text-xs">ENS</span>
                <span className="text-sm text-zinc-400">Deep Ensemble Synthesizer</span>
              </div>
              <Badge variant="success">Active</Badge>
            </div>
            
            {/* Raw JSON Debug toggle could go here if needed */}
          </div>
        </div>
      )}
    </Card>
  );
}
