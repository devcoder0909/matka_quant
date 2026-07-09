// ─── Market Types ────────────────────────────────────────────────────────────

export interface Market {
  id: number;
  name: string;
  code: string;
  display_name: string;
  is_active: boolean;
}

// ─── Import & Data Quality Types ─────────────────────────────────────────────

export interface ImportStats {
  total_records: number;
  valid_records: number;
  duplicate_records: number;
  invalid_records: number;
  missing_records: number;
  data_quality_score: number;
  data_completeness_score: number;
  last_result_date: string;
}

export interface ImportHistoryEntry {
  id: number;
  created_at: string;
  source_type: string;
  market_code: string;
  records_imported: number;
  quality_score: number;
  status: 'completed' | 'failed' | 'processing';
  error_message?: string;
}

// ─── Analysis Types ──────────────────────────────────────────────────────────

export interface Candidate {
  candidate_type: string;
  candidate_value: string;
  research_score: number;
  model_probability: number;
  baseline_probability: number;
  confidence_level: string;
  supporting_signals: string[];
  conflicting_signals: string[];
  explanation: Record<string, unknown>;
  sample_size: number;
  stability_level: string;
}

export interface FrequencyData {
  digit: number;
  count: number;
  percentage: number;
  status: 'hot' | 'cold' | 'overdue' | 'normal';
  last_seen: string;
  gap: number;
}

export interface AnalysisResult {
  run_id: number;
  market: string;
  target_date: string;
  status: string;
  candidates: {
    ank: Candidate[];
    jodi: Candidate[];
    patti: Candidate[];
  };
  frequency_data: FrequencyData[];
}

// ─── Command Types ───────────────────────────────────────────────────────────

export interface CommandResponse {
  success: boolean;
  message: string;
  data?: unknown;
}

// ─── Historical Data Types ───────────────────────────────────────────────────

export interface HistoricalRecord {
  id: number;
  date: string;
  market_code: string;
  open_patti: string;
  open_ank: string;
  jodi: string;
  close_ank: string;
  close_patti: string;
  is_validated: boolean;
}

// ─── UI State Types ──────────────────────────────────────────────────────────

export type NavSection =
  | 'dashboard'
  | 'import'
  | 'analysis'
  | 'frequency'
  | 'backtest'
  | 'history'
  | 'settings';

export type CandidateTab = 'ank' | 'jodi' | 'patti';

export type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

export type ButtonVariant = 'primary' | 'secondary' | 'danger';

export type FrequencyWindow = 7 | 14 | 21 | 30 | 50 | 90 | 180 | 0;
