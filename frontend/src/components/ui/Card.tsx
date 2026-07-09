'use client';

import React from 'react';

interface CardProps {
  title?: string;
  subtitle?: string;
  glow?: boolean;
  className?: string;
  headerRight?: React.ReactNode;
  children: React.ReactNode;
  id?: string;
}

export default function Card({
  title,
  subtitle,
  glow = false,
  className = '',
  headerRight,
  children,
  id,
}: CardProps) {
  return (
    <div
      id={id}
      className={`${glow ? 'glass-card-glow' : 'glass-card'} p-5 animate-fade-in ${className}`}
    >
      {(title || headerRight) && (
        <div className="flex items-start justify-between mb-4">
          <div>
            {title && (
              <h3 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>
            )}
          </div>
          {headerRight && <div>{headerRight}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
