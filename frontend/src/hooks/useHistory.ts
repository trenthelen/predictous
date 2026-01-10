import { useState, useCallback } from 'react';
import { fetchHistory, ApiError } from '../api/client';
import type { HistoryItem } from '../types/api';

interface UseHistoryResult {
  items: HistoryItem[];
  loading: boolean;
  error: ApiError | null;
  load: () => void;
}

export function useHistory(): UseHistoryResult {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchHistory();
      setItems(response.items);
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError(0, String(e)));
    } finally {
      setLoading(false);
    }
  }, []);

  return { items, loading, error, load };
}
