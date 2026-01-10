import type { AgentFailure } from '../types/api';

interface FailureDisplayProps {
  failures: AgentFailure[];
}

export function FailureDisplay({ failures }: FailureDisplayProps) {
  if (failures.length === 0) return null;

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-amber-700 dark:text-amber-400">
        Agent Failures ({failures.length})
      </h3>
      <div className="space-y-2">
        {failures.map((failure, index) => (
          <div
            key={`${failure.miner_uid}-${index}`}
            className="rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-900 dark:bg-amber-900/20"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-amber-800 dark:text-amber-200">
                Rank {failure.rank + 1} (UID {failure.miner_uid})
              </span>
              {failure.error_type && (
                <span className="rounded bg-amber-200 px-2 py-0.5 text-xs text-amber-800 dark:bg-amber-800 dark:text-amber-200">
                  {failure.error_type}
                </span>
              )}
            </div>
            <p className="mt-1 text-sm text-amber-700 dark:text-amber-300">{failure.error}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
