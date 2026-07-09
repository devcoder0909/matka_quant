'use client';

import React, { useState } from 'react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { importChart } from '@/lib/api';
import type { ImportStats } from '@/lib/types';

export default function ChartInput({ onImportSuccess }: { onImportSuccess?: () => void }) {
  const [rawHtml, setRawHtml] = useState('');
  const [marketCode, setMarketCode] = useState('');
  const [isImporting, setIsImporting] = useState(false);
  const [result, setResult] = useState<{ message: string; stats: ImportStats } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleImport = async () => {
    if (!rawHtml.trim()) return;

    setIsImporting(true);
    setError(null);
    setResult(null);

    try {
      const res = await importChart(rawHtml, marketCode || undefined);
      setResult(res);
      setRawHtml('');
      if (onImportSuccess) onImportSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed');
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <Card
      id="chart-input"
      title="Chart Data Import"
      subtitle="Paste chart HTML or formatted text data"
    >
      <div className="space-y-4">
        {/* Market Code Input */}
        <div>
          <label
            htmlFor="chart-market-code"
            className="block text-xs font-medium text-gray-400 mb-1.5"
          >
            Market Code (optional — auto-detected if omitted)
          </label>
          <input
            id="chart-market-code"
            type="text"
            value={marketCode}
            onChange={(e) => setMarketCode(e.target.value)}
            placeholder="e.g., KALYAN, MAIN_MUMBAI"
            className="w-full px-3 py-2 bg-black/30 border border-gray-700/50 rounded-lg text-sm text-gray-300 placeholder:text-gray-600 focus-ring outline-none transition-colors focus:border-cyan-500/30"
          />
        </div>

        {/* Textarea */}
        <div>
          <label
            htmlFor="chart-raw-data"
            className="block text-xs font-medium text-gray-400 mb-1.5"
          >
            Raw Chart Data
          </label>
          <textarea
            id="chart-raw-data"
            value={rawHtml}
            onChange={(e) => setRawHtml(e.target.value)}
            rows={8}
            placeholder={`Paste chart data here. Supported formats:\n\n• HTML table from chart websites\n• Tab-separated text (Date  Open  Close)\n• CSV format (Date,Open_Patti,Close_Patti)\n• Plain text with date and result patterns\n\nThe system will auto-detect the format and parse accordingly.`}
            className="w-full px-3 py-3 bg-black/30 border border-gray-700/50 rounded-lg text-sm font-mono text-gray-300 placeholder:text-gray-600 focus-ring outline-none resize-y min-h-[120px] transition-colors focus:border-cyan-500/30"
          />
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <Button
            id="import-chart-btn"
            onClick={handleImport}
            loading={isImporting}
            disabled={!rawHtml.trim() || isImporting}
          >
            {isImporting ? 'Importing Data... Please wait' : 'Import Chart'}
          </Button>
          {rawHtml.trim() && (
            <span className="text-xs text-gray-500">
              {rawHtml.length.toLocaleString()} characters
            </span>
          )}
        </div>

        {/* Result */}
        {result && (
          <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 animate-fade-in">
            <p className="text-sm text-emerald-400 font-medium">{result.message}</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-2">
              <div className="text-center">
                <div className="text-lg font-bold font-mono-data text-white">
                  {result.stats.total_records}
                </div>
                <div className="text-[10px] text-gray-500 uppercase">Total</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold font-mono-data text-emerald-400">
                  {result.stats.valid_records}
                </div>
                <div className="text-[10px] text-gray-500 uppercase">Valid</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold font-mono-data text-amber-400">
                  {result.stats.duplicate_records}
                </div>
                <div className="text-[10px] text-gray-500 uppercase">Duplicates</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold font-mono-data text-rose-400">
                  {result.stats.invalid_records}
                </div>
                <div className="text-[10px] text-gray-500 uppercase">Invalid</div>
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 animate-fade-in">
            <p className="text-sm text-rose-400">✗ {error}</p>
          </div>
        )}
      </div>
    </Card>
  );
}
