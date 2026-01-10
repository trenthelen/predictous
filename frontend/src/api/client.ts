import type {
  HealthResponse,
  AgentsResponse,
  PredictionRequest,
  PredictionMode,
  ErrorCode,
  JobResponse,
  JobStatusResponse,
} from '../types/api';

// Use /api proxy in dev (handles long timeouts), direct URL in production
const API_BASE = import.meta.env.VITE_API_URL || '/api';

export class ApiError extends Error {
  status: number;
  errorCode?: ErrorCode;

  constructor(status: number, message: string, errorCode?: ErrorCode) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.errorCode = errorCode;
  }
}

export function getErrorMessage(error: ApiError): string {
  switch (error.errorCode) {
    case 'rate_limit_exceeded':
      return 'You have reached your daily request limit. Please try again tomorrow.';
    case 'budget_exceeded':
      return 'The service has reached its daily capacity. Please try again tomorrow.';
    case 'queue_full':
      return 'The server is currently busy. Please wait a moment and try again.';
    default:
      return error.message || 'An unexpected error occurred. Please try again.';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorCode: ErrorCode | undefined;
    let message = `HTTP ${response.status}`;

    try {
      const data = await response.json();
      if (data.detail) {
        message = data.detail.message || message;
        errorCode = data.detail.error_code;
      }
    } catch {
      // Ignore JSON parse errors
    }

    throw new ApiError(response.status, message, errorCode);
  }

  return response.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`);
  return handleResponse<HealthResponse>(response);
}

export async function fetchAgents(): Promise<AgentsResponse> {
  const response = await fetch(`${API_BASE}/agents`);
  return handleResponse<AgentsResponse>(response);
}

export async function submitPrediction(
  mode: PredictionMode,
  request: PredictionRequest,
  minerUid?: number
): Promise<JobResponse> {
  const url =
    mode === 'selected'
      ? `${API_BASE}/predict/selected/${minerUid}`
      : `${API_BASE}/predict/${mode}`;

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  return handleResponse<JobResponse>(response);
}

export async function fetchJobStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(`${API_BASE}/predict/status/${jobId}`);
  return handleResponse<JobStatusResponse>(response);
}
