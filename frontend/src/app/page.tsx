"use client";

import React, { useState, useEffect } from 'react';
import Header from '../components/layout/Header';
import Sidebar from '../components/layout/Sidebar';
import CommandInput from '../components/input/CommandInput';
import ChartInput from '../components/input/ChartInput';
import FileUpload from '../components/input/FileUpload';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import PredictionMatrix from '../components/analysis/PredictionMatrix';
import BacktestTerminal from '../components/analysis/BacktestTerminal';
import type { NavSection } from '@/lib/types';

export default function Dashboard() {
  const [activeMarket, setActiveMarket] = useState("KALYAN");
  const [activeSection, setActiveSection] = useState<NavSection>("dashboard");
  
  return (
    <div className="flex h-screen bg-background text-zinc-300 font-sans overflow-hidden">
      <Sidebar activeSection={activeSection} onNavigate={setActiveSection} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-6 bg-[#0a0e1a]">
          <div className="max-w-7xl mx-auto space-y-6 animate-fade-in">
            
            {/* Header Section */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 mb-8">
              <div>
                <h1 className="text-4xl font-black tracking-tight mb-2">
                  MATKA <span className="text-gradient">QUANTUM AI</span>
                </h1>
                <p className="text-zinc-400 font-mono text-sm">
                  PROJECT TRINETRA // INTELLIGENCE DASHBOARD
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant="neutral" dot pulse>SYSTEM ONLINE</Badge>
                <div className="text-xs font-mono text-zinc-500 bg-black/30 px-3 py-1.5 rounded-full border border-white/5">
                  MODEL: TR-2026.4
                </div>
              </div>
            </div>

            {/* Main Analysis Dashboard (Phase 2 Grid) */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <PredictionMatrix />
                <BacktestTerminal />
              </div>
              
              <div className="space-y-6">
                <CommandInput />
                <FileUpload />
                <ChartInput />
              </div>
            </div>
            
            {/* Quick Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card title="Active Market" className="bg-card/80 backdrop-blur">
                <div className="text-3xl font-bold text-primary-400">{activeMarket}</div>
                <div className="text-sm text-zinc-500 mt-1">Status: Open</div>
              </Card>
              <Card title="Data Quality" className="bg-card/80 backdrop-blur">
                <div className="text-3xl font-bold text-success-400">98.5%</div>
                <div className="text-sm text-zinc-500 mt-1">Validated Records</div>
              </Card>
              <Card title="Last Analysis" className="bg-card/80 backdrop-blur">
                <div className="text-3xl font-bold text-zinc-100">Today</div>
                <div className="text-sm text-zinc-500 mt-1">Full frequency scan</div>
              </Card>
              <Card title="System Load" className="bg-card/80 backdrop-blur">
                <div className="text-3xl font-bold text-emerald-400">Normal</div>
                <div className="text-sm text-zinc-500 mt-1">All modules online</div>
              </Card>
            </div>

            
            {/* Placeholder for Research Watchlist (Phase 1 Output) */}
            <Card title="Research Watchlist — Candidates" className="min-h-[300px]">
              <div className="flex items-center justify-between mb-4">
                <div className="space-x-2">
                  <Button variant="primary" size="sm">Ank Candidates</Button>
                  <Button variant="secondary" size="sm">Jodi Candidates</Button>
                  <Button variant="secondary" size="sm">Patti Candidates</Button>
                </div>
                <Badge variant="warning">Statistical Research Only</Badge>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                 <div className="p-4 bg-black/40 rounded-lg border border-zinc-800">
                    <div className="text-sm text-zinc-400 mb-1">Top Ank Candidate</div>
                    <div className="text-5xl font-bold text-white mb-3">6</div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-zinc-500">Research Score</span>
                      <span className="text-primary-400 font-mono">87/100</span>
                    </div>
                    <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-primary-400 h-full w-[87%]"></div>
                    </div>
                 </div>
                 
                 <div className="p-4 bg-black/40 rounded-lg border border-zinc-800">
                    <div className="text-sm text-zinc-400 mb-1">Top Jodi Candidate</div>
                    <div className="text-5xl font-bold text-white mb-3">65</div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-zinc-500">Research Score</span>
                      <span className="text-primary-400 font-mono">72/100</span>
                    </div>
                    <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-primary-400 h-full w-[72%]"></div>
                    </div>
                 </div>
                 
                 <div className="p-4 bg-black/40 rounded-lg border border-zinc-800">
                    <div className="text-sm text-zinc-400 mb-1">Top Open Patti</div>
                    <div className="text-5xl font-bold text-white mb-3">123</div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-zinc-500">Research Score</span>
                      <span className="text-primary-400 font-mono">68/100</span>
                    </div>
                    <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-primary-400 h-full w-[68%]"></div>
                    </div>
                 </div>
              </div>
            </Card>

          </div>
        </main>
      </div>
    </div>
  );
}
