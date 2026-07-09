"use client";

import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

export default function PredictionMatrix() {
  const [activeTab, setActiveTab] = useState('jodi');

  return (
    <Card title="Quantum Prediction Matrix" glow className="w-full h-full min-h-[400px]">
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
        <Badge variant="success" pulse>LIVE PREDICTION AI</Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Top Prediction */}
        <div className="flex flex-col items-center justify-center p-8 border border-cyan-500/30 rounded-xl bg-cyan-950/20 shadow-[0_0_30px_rgba(34,211,238,0.1)] relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-400 to-emerald-400"></div>
          <span className="text-zinc-400 text-sm tracking-widest uppercase mb-2">Highest Probability</span>
          <span className="text-8xl font-black text-transparent bg-clip-text bg-gradient-to-br from-white to-cyan-400">
            {activeTab === 'jodi' ? '65' : '6'}
          </span>
          
          <div className="mt-6 flex flex-col w-full gap-2">
            <div className="flex justify-between text-sm">
              <span className="text-zinc-500">Confidence Score</span>
              <span className="text-cyan-400 font-mono">87.4%</span>
            </div>
            <div className="w-full bg-black/50 h-2 rounded-full overflow-hidden">
              <div className="bg-gradient-to-r from-cyan-500 to-emerald-400 h-full w-[87.4%]"></div>
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
            <Badge variant="success">High</Badge>
          </div>

          <div className="p-3 rounded-lg bg-black/40 border border-white/5 flex justify-between items-center">
            <div className="flex items-center gap-3">
              <span className="w-8 h-8 rounded bg-zinc-800 flex items-center justify-center font-mono text-xs">M-C</span>
              <span className="text-sm text-zinc-400">Markov Chain Match</span>
            </div>
            <Badge variant="warning">Moderate</Badge>
          </div>
          
          <div className="p-3 rounded-lg bg-black/40 border border-white/5 flex justify-between items-center">
            <div className="flex items-center gap-3">
              <span className="w-8 h-8 rounded bg-zinc-800 flex items-center justify-center font-mono text-xs">S-D</span>
              <span className="text-sm text-zinc-400">Standard Deviation Gap</span>
            </div>
            <Badge variant="danger">Overdue</Badge>
          </div>
        </div>
      </div>
    </Card>
  );
}
