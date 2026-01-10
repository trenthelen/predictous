import { useState, useEffect } from 'react';
import { fetchAgents, ApiError } from '../api/client';
import type { AgentInfo } from '../types/api';

interface UseAgentsResult {
  agents: AgentInfo[];
  loading: boolean;
  error: ApiError | null;
  refetch: () => void;
}

export function useAgents(): UseAgentsResult {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const loadAgents = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchAgents();
      setAgents(response.agents);
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError(0, String(e)));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
  }, []);

  return { agents, loading, error, refetch: loadAgents };
}
