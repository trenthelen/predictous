// Request types
export interface PredictionRequest {
  question: string;
  resolution_criteria: string;
  resolution_date?: string;
  categories: string[];
}

export type PredictionMode = 'champion' | 'council' | 'selected';

// Response types
export interface HealthResponse {
  status: string;
  requests_used: number;
  requests_limit: number;
  requests_remaining: number;
}

export interface AgentInfo {
  miner_uid: number;
  rank: number;
  weight: number;
  avg_brier: number;
  accuracy: number;
}

export interface AgentsResponse {
  agents: AgentInfo[];
}

export interface AgentPrediction {
  miner_uid: number;
  rank: number;
  version_id: string;
  prediction: number;
  reasoning: string | null;
  cost: number;
}

export interface AgentFailure {
  miner_uid: number;
  rank: number;
  error: string;
  error_type: string | null;
}

export interface PredictResponse {
  request_id: string;
  status: 'success' | 'error';
  prediction: number | null;
  agent_predictions: AgentPrediction[];
  failures: AgentFailure[];
  total_cost: number;
  error: string | null;
}

export type ErrorCode = 'rate_limit_exceeded' | 'budget_exceeded' | 'queue_full' | 'request_in_progress';

// Async job types
export interface JobResponse {
  job_id: string;
}

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  result: PredictResponse | null;
  error: string | null;
}

// History types
export interface HistoryItem {
  request_id: string;
  question: string;
  prediction: number | null;
  timestamp: string;
}

export interface HistoryResponse {
  items: HistoryItem[];
}

// Prediction detail types
export interface AgentPredictionDetail {
  prediction: number | null;
  reasoning: string | null;
  cost: number;
  status: string;
  error: string | null;
}

export interface PredictionDetail {
  request_id: string;
  question: string;
  resolution_criteria: string;
  resolution_date: string | null;
  categories: string | null;
  prediction: number | null;
  agent_predictions: AgentPredictionDetail[];
  timestamp: string;
}
