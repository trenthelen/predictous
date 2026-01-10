import { useState, useCallback, useRef } from 'react';
import { predict, ApiError } from '../api/client';
import type { PredictionRequest, PredictResponse, PredictionMode } from '../types/api';

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
    stopTimer();
    setResult(null);
    setError(null);
    setElapsed(0);
  }, []);

  const submit = useCallback(
    async (mode: PredictionMode, request: PredictionRequest, minerUid?: number) => {
      reset();
      setLoading(true);
      startTimer();

      try {
        const response = await predict(mode, request, minerUid);
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
