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

export type ErrorCode = 'rate_limit_exceeded' | 'budget_exceeded' | 'queue_full';

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
