'use client';

import React from 'react';
import type { BadgeVariant } from '@/lib/types';

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
  dot?: boolean;
  pulse?: boolean;
}

const variantStyles: Record<BadgeVariant, string> = {
  success:
    'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
  warning:
    'bg-amber-500/15 text-amber-400 border-amber-500/20',
  danger:
    'bg-rose-500/15 text-rose-400 border-rose-500/20',
  info:
    'bg-cyan-500/15 text-cyan-400 border-cyan-500/20',
  neutral:
    'bg-gray-500/15 text-gray-400 border-gray-500/20',
};

const dotColors: Record<BadgeVariant, string> = {
  success: 'bg-emerald-400',
  warning: 'bg-amber-400',
  danger: 'bg-rose-400',
  info: 'bg-cyan-400',
  neutral: 'bg-gray-400',
};

export default function Badge({
  variant = 'neutral',
  children,
  className = '',
  dot = false,
  pulse = false,
}: BadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center gap-1.5 px-2.5 py-0.5
        text-xs font-medium rounded-full border
        ${variantStyles[variant]}
        ${className}
      `}
    >
      {dot && (
        <span className="relative flex h-1.5 w-1.5">
          {pulse && (
            <span
              className={`absolute inset-0 rounded-full ${dotColors[variant]} animate-ping opacity-75`}
            />
          )}
          <span
            className={`relative inline-flex h-1.5 w-1.5 rounded-full ${dotColors[variant]}`}
          />
        </span>
      )}
      {children}
    </span>
  );
}
