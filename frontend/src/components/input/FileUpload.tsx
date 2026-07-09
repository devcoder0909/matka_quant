'use client';

import React, { useState, useRef, useCallback } from 'react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { uploadFile } from '@/lib/api';
import type { ImportStats } from '@/lib/types';

const ACCEPTED_TYPES = ['.csv', '.json', '.html', '.txt'];

export default function FileUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<{ message: string; stats: ImportStats } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = (f: File) => {
    const ext = '.' + f.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED_TYPES.includes(ext)) {
      setError(`Unsupported file type: ${ext}. Accepted: ${ACCEPTED_TYPES.join(', ')}`);
      return;
    }
    setFile(f);
    setError(null);
    setResult(null);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);
    setResult(null);
    setProgress(10);

    try {
      const progressInterval = setInterval(() => {
        setProgress((p) => Math.min(p + 15, 85));
      }, 300);

      const res = await uploadFile(file);

      clearInterval(progressInterval);
      setProgress(100);
      setResult(res);
      setFile(null);

      setTimeout(() => setProgress(0), 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      setProgress(0);
    } finally {
      setIsUploading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  return (
    <Card
      id="file-upload"
      title="File Upload"
      subtitle="Upload CSV, JSON, HTML, or TXT files"
    >
      <div className="space-y-4">
        {/* Drop Zone */}
        <div
          id="file-drop-zone"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => inputRef.current?.click()}
          className={`
            relative cursor-pointer rounded-lg border-2 border-dashed p-8
            transition-all duration-200 text-center
            ${isDragging
              ? 'border-cyan-400 bg-cyan-500/5'
              : 'border-gray-700/50 hover:border-gray-600/50 hover:bg-white/[0.02]'
            }
          `}
        >
          <input
            ref={inputRef}
            id="file-input"
            type="file"
            accept={ACCEPTED_TYPES.join(',')}
            onChange={(e) => {
              if (e.target.files?.[0]) handleFile(e.target.files[0]);
            }}
            className="hidden"
          />

          <div className="text-3xl mb-2">{isDragging ? '⬇️' : '📁'}</div>
          <p className="text-sm text-gray-300 font-medium">
            {isDragging ? 'Drop file here' : 'Drag & drop a file, or click to browse'}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {ACCEPTED_TYPES.join(', ')} — Max 10MB
          </p>
        </div>

        {/* Selected File */}
        {file && (
          <div className="flex items-center justify-between p-3 rounded-lg bg-gray-800/50 border border-gray-700/30 animate-fade-in">
            <div className="flex items-center gap-3 min-w-0">
              <span className="text-lg">📄</span>
              <div className="min-w-0">
                <p className="text-sm text-gray-200 font-medium truncate">
                  {file.name}
                </p>
                <p className="text-xs text-gray-500">
                  {formatFileSize(file.size)}
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                setFile(null);
                setError(null);
              }}
              className="text-gray-500 hover:text-gray-300 p-1 transition-colors flex-shrink-0"
              aria-label="Remove file"
            >
              ✕
            </button>
          </div>
        )}

        {/* Progress Bar */}
        {progress > 0 && (
          <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-500 to-emerald-500 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        {/* Upload Button */}
        {file && (
          <Button
            id="upload-btn"
            onClick={handleUpload}
            loading={isUploading}
            fullWidth
          >
            Upload & Import
          </Button>
        )}

        {/* Result */}
        {result && (
          <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 animate-fade-in">
            <p className="text-sm text-emerald-400 font-medium">{result.message}</p>
            <p className="text-xs text-gray-400 mt-1">
              {result.stats.valid_records} valid records imported •
              Quality score: {(result.stats.data_quality_score * 100).toFixed(0)}%
            </p>
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
