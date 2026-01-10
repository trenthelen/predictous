import type { AgentFailure } from '../types/api';

interface FailureDisplayProps {
  failures: AgentFailure[];
}

export function FailureDisplay({ failures }: FailureDisplayProps) {
  if (failures.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="font-mono text-xs text-muted-amber">
        FAILURES ({failures.length})
      </div>
      <div className="space-y-2">
        {failures.map((failure, index) => (
          <div
            key={`${failure.miner_uid}-${index}`}
            className="border border-muted-amber/30 bg-muted-amber/5 px-4 py-3"
          >
            <div className="flex items-center justify-between font-mono text-xs">
              <span className="text-teal-800 dark:text-cream-100">
                RANK {failure.rank + 1} / UID {failure.miner_uid}
              </span>
              {failure.error_type && (
                <span className="text-muted-amber">{failure.error_type}</span>
              )}
            </div>
            <p className="mt-2 text-xs text-teal-600/80 dark:text-cream-300/80">
              {failure.error}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
