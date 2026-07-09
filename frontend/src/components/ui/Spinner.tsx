'use client';

import React from 'react';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizes = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
};

export default function Spinner({ size = 'md', className = '' }: SpinnerProps) {
  return (
    <div className={`flex items-center justify-center ${className}`}>
      <svg
        className={`animate-spin ${sizes[size]} text-cyan-400`}
        viewBox="0 0 24 24"
        fill="none"
      >
        <circle
          className="opacity-20"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="3"
        />
        <path
          className="opacity-80"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
    </div>
  );
}

export function SkeletonLine({ className = '' }: { className?: string }) {
  return <div className={`skeleton-shimmer h-4 ${className}`} />;
}

export function SkeletonCard({ lines = 3 }: { lines?: number }) {
  return (
    <div className="glass-card p-5 space-y-3">
      <div className="skeleton-shimmer h-5 w-1/3" />
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="skeleton-shimmer h-4"
          style={{ width: `${70 + Math.random() * 30}%` }}
        />
      ))}
    </div>
  );
}
