import { useState, useEffect, useCallback } from 'react';
import { fetchHealth, ApiError } from '../api/client';
import type { HealthResponse } from '../types/api';

interface UseHealthResult {
  health: HealthResponse | null;
  loading: boolean;
  error: ApiError | null;
  refetch: () => void;
}

export function useHealth(): UseHealthResult {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchHealth();
      setHealth(response);
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError(0, String(e)));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { health, loading, error, refetch: fetch };
}
