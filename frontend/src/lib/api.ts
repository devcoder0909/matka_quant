const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://matka-quant.onrender.com/api/v1';

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorBody = await response.text().catch(() => 'Unknown error');
    throw new Error(
      `API Error ${response.status}: ${response.statusText} — ${errorBody}`
    );
  }

  return response.json() as Promise<T>;
}

// ─── Markets ─────────────────────────────────────────────────────────────────

import type {
  Market,
  ImportStats,
  AnalysisResult,
  CommandResponse,
  ImportHistoryEntry,
  HistoricalRecord,
} from './types';

export async function getMarkets(): Promise<Market[]> {
  return fetchApi<Market[]>('/markets');
}

// ─── Import ──────────────────────────────────────────────────────────────────

export async function importChart(
  rawHtml: string,
  marketCode?: string
): Promise<{ message: string; stats: ImportStats }> {
  return fetchApi('/import/chart', {
    method: 'POST',
    body: JSON.stringify({ raw_html: rawHtml, market_code: marketCode }),
  });
}

export async function uploadFile(
  file: File
): Promise<{ message: string; stats: ImportStats }> {
  const formData = new FormData();
  formData.append('file', file);

  const url = `${BASE_URL}/import/file`;
  const response = await fetch(url, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorBody = await response.text().catch(() => 'Unknown error');
    throw new Error(
      `API Error ${response.status}: ${response.statusText} — ${errorBody}`
    );
  }

  return response.json();
}

// ─── Analysis ────────────────────────────────────────────────────────────────

export async function runAnalysis(
  marketCode: string,
  targetDate: string
): Promise<any> {
  return fetchApi<any>('/analysis/run', {
    method: 'POST',
    body: JSON.stringify({ market_code: marketCode, target_date: targetDate }),
  });
}

export async function runBacktest(
  marketCode: string,
  days: number = 30
): Promise<any> {
  return fetchApi<any>(`/backtest/run/${marketCode}?days=${days}`, {
    method: 'POST',
  });
}

export async function getAnalysisResult(
  runId: number
): Promise<AnalysisResult> {
  return fetchApi<AnalysisResult>(`/analysis/result/${runId}`);
}

// ─── Commands ────────────────────────────────────────────────────────────────

export async function executeCommand(
  command: string
): Promise<CommandResponse> {
  return fetchApi<CommandResponse>('/command', {
    method: 'POST',
    body: JSON.stringify({ command }),
  });
}

// ─── History ─────────────────────────────────────────────────────────────────

export async function getImportHistory(): Promise<ImportHistoryEntry[]> {
  return fetchApi<ImportHistoryEntry[]>('/import/history');
}

export async function getHistoricalRecords(
  marketCode: string,
  page: number = 1,
  pageSize: number = 50
): Promise<{ records: HistoricalRecord[]; total: number }> {
  return fetchApi(`/data/${marketCode}/records?page=${page}&page_size=${pageSize}`);
}

export async function getImportStats(
  marketCode: string
): Promise<ImportStats> {
  return fetchApi<ImportStats>(`/data/${marketCode}/stats`);
}

export async function getFrequencyData(
  marketCode: string,
  window: number = 30,
  digitType: string = 'ank'
): Promise<unknown> {
  return fetchApi(`/analysis/${marketCode}/frequency?window=${window}&digit_type=${digitType}`);
}
