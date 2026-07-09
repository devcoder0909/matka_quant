'use client';

import React, { useState } from 'react';
import type { NavSection } from '@/lib/types';

interface SidebarProps {
  activeSection: NavSection;
  onNavigate: (section: NavSection) => void;
}

interface NavItem {
  id: NavSection;
  label: string;
  icon: string;
}

const navItems: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
  { id: 'import', label: 'Import Data', icon: '📥' },
  { id: 'analysis', label: 'Analysis', icon: '🔬' },
  { id: 'frequency', label: 'Frequency Charts', icon: '📈' },
  { id: 'backtest', label: 'Backtest Lab', icon: '🧪' },
  { id: 'history', label: 'Import History', icon: '📋' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
];

export default function Sidebar({ activeSection, onNavigate }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <>
      {/* Mobile Overlay */}
      <div className="lg:hidden fixed top-14 left-0 z-40">
        <button
          id="sidebar-toggle"
          onClick={() => setCollapsed(!collapsed)}
          className="m-2 p-2 rounded-lg bg-gray-800/80 backdrop-blur border border-gray-700/50 text-gray-400 hover:text-white transition-colors"
          aria-label="Toggle sidebar"
        >
          <span className="text-lg">{collapsed ? '☰' : '✕'}</span>
        </button>
      </div>

      {/* Sidebar */}
      <aside
        id="sidebar"
        className={`
          fixed lg:sticky top-14 left-0 z-30
          h-[calc(100vh-3.5rem)]
          border-r border-white/5
          bg-[#0a0e1a]/95 backdrop-blur-xl
          transition-all duration-200 ease-out
          ${collapsed ? 'w-16' : 'w-56'}
          ${collapsed ? '-translate-x-full lg:translate-x-0' : 'translate-x-0'}
          flex flex-col
        `}
      >
        {/* Nav Items */}
        <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <button
              key={item.id}
              id={`nav-${item.id}`}
              onClick={() => {
                onNavigate(item.id);
                if (window.innerWidth < 1024) setCollapsed(true);
              }}
              className={`
                nav-item w-full flex items-center gap-3 px-3 py-2.5
                text-sm font-medium
                ${activeSection === item.id
                  ? 'active text-cyan-400'
                  : 'text-gray-400 hover:text-gray-200'
                }
              `}
              title={collapsed ? item.label : undefined}
            >
              <span className="text-base flex-shrink-0 w-6 text-center">
                {item.icon}
              </span>
              {!collapsed && (
                <span className="truncate">{item.label}</span>
              )}
            </button>
          ))}
        </nav>

        {/* Collapse Toggle (Desktop) */}
        <div className="hidden lg:block p-2 border-t border-white/5">
          <button
            id="sidebar-collapse"
            onClick={() => setCollapsed(!collapsed)}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-gray-800/50 transition-colors text-xs"
          >
            <span>{collapsed ? '→' : '←'}</span>
            {!collapsed && <span>Collapse</span>}
          </button>
        </div>
      </aside>
    </>
  );
}
