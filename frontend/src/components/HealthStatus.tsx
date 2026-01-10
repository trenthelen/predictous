import { useHealth } from '../hooks/useHealth';

export function HealthStatus() {
  const { health, loading } = useHealth();

  if (loading || !health) {
    return (
      <div className="text-sm text-gray-500 dark:text-gray-400">
        Loading...
      </div>
    );
  }

  const percentage = Math.round((health.requests_remaining / health.requests_limit) * 100);

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-gray-600 dark:text-gray-400">Quota:</span>
      <div className="flex items-center gap-1">
        <div className="h-2 w-16 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
          <div
            className="h-full bg-primary-500 transition-all"
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span className="text-gray-900 dark:text-white">
          {health.requests_remaining}/{health.requests_limit}
        </span>
      </div>
    </div>
  );
}
