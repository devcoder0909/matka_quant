'use client';

import React from 'react';

export default function Header() {
  return (
    <header
      id="header"
      className="sticky top-0 z-50 w-full border-b border-white/5 bg-[#0a0e1a]/80 backdrop-blur-xl"
    >
      <div className="flex items-center justify-between h-14 px-4 lg:px-6">
        {/* Logo & Title */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-emerald-400 flex items-center justify-center text-sm font-bold text-gray-900">
              Q
            </div>
            <div className="hidden sm:block">
              <h1 className="text-sm font-bold tracking-widest text-gradient leading-none">
                MATKA QUANTUM AI
              </h1>
              <p className="text-[10px] text-gray-500 tracking-wider mt-0.5">
                Project Trinetra — Statistical Research Engine
              </p>
            </div>
          </div>
        </div>

        {/* Status Indicator */}
        <div className="flex items-center gap-3">
          <div
            id="system-status"
            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20"
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inset-0 rounded-full bg-emerald-400 animate-pulse-live" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
            </span>
            <span className="text-[10px] font-semibold tracking-widest text-emerald-400 uppercase">
              System Online
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
