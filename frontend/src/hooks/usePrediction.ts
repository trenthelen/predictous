import { useState, useCallback, useRef } from 'react';
import { submitPrediction, fetchJobStatus, ApiError } from '../api/client';
import type { PredictionRequest, PredictResponse, PredictionMode } from '../types/api';

const POLL_INTERVAL_MS = 2000;

interface UsePredictionResult {
  submit: (mode: PredictionMode, request: PredictionRequest, minerUid?: number) => Promise<void>;
  result: PredictResponse | null;
  loading: boolean;
  error: ApiError | null;
  elapsed: number;
  reset: () => void;
}

export function usePrediction(): UsePredictionResult {
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef<number | null>(null);
  const pollingRef = useRef<boolean>(false);

  const startTimer = () => {
    setElapsed(0);
    timerRef.current = window.setInterval(() => {
      setElapsed((e) => e + 1);
    }, 1000);
  };

  const stopTimer = () => {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const reset = useCallback(() => {
    pollingRef.current = false;
    stopTimer();
    setResult(null);
    setError(null);
    setElapsed(0);
  }, []);

  const pollForResult = async (jobId: string): Promise<PredictResponse> => {
    pollingRef.current = true;

    while (pollingRef.current) {
      const status = await fetchJobStatus(jobId);

      if (status.status === 'completed' && status.result) {
        return status.result;
      }

      if (status.status === 'failed') {
        throw new ApiError(500, status.error || 'Prediction failed');
      }

      // Wait before next poll
      await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
    }

    throw new ApiError(0, 'Polling cancelled');
  };

  const submit = useCallback(
    async (mode: PredictionMode, request: PredictionRequest, minerUid?: number) => {
      reset();
      setLoading(true);
      startTimer();

      try {
        // Submit and get job_id
        const { job_id } = await submitPrediction(mode, request, minerUid);

        // Poll for result
        const response = await pollForResult(job_id);
        setResult(response);
      } catch (e) {
        setError(e instanceof ApiError ? e : new ApiError(0, String(e)));
      } finally {
        setLoading(false);
        stopTimer();
      }
    },
    [reset]
  );

  return { submit, result, loading, error, elapsed, reset };
}
