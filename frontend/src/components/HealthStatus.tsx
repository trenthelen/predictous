import { useHealth } from '../hooks/useHealth';

export function HealthStatus() {
  const { health, loading } = useHealth();

  if (loading || !health) {
    return (
      <span className="font-mono text-xs text-teal-600/40 dark:text-cream-300/40">
        ...
      </span>
    );
  }

  return (
    <div className="flex items-center gap-2 font-mono text-xs">
      <span className="text-teal-600/60 dark:text-cream-300/60">QUOTA</span>
      <span className="text-teal-800 dark:text-cream-100">
        {health.requests_remaining}/{health.requests_limit}
      </span>
    </div>
  );
}
