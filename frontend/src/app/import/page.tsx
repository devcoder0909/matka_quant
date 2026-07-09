"use client";

import React from 'react';
import ChartInput from '../../components/input/ChartInput';
import FileUpload from '../../components/input/FileUpload';

export default function ImportPage() {
  return (
    <div className="min-h-screen bg-[#0a0e1a] text-zinc-300 font-sans p-8">
      <div className="max-w-3xl mx-auto space-y-8">
        <h1 className="text-3xl font-bold text-white mb-8">Hidden Import Gateway</h1>
        <ChartInput />
        <FileUpload />
      </div>
    </div>
  );
}
