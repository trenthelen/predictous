import { useEffect } from 'react';
import { useHistory } from '../hooks/useHistory';
import { formatPercentage, formatTimestamp, truncate } from '../utils/format';

export function History() {
  const { items, loading, error, load } = useHistory();

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="font-mono text-sm text-teal-600/60 dark:text-cream-300/60">
          Loading...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="font-mono text-sm text-muted-red">
          Failed to load history
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="font-mono text-4xl text-teal-600/20 dark:text-cream-300/20">
          []
        </div>
        <h2 className="mt-6 font-mono text-xl tracking-tight text-teal-800 dark:text-cream-100">
          NO PREDICTIONS YET
        </h2>
        <p className="mt-3 max-w-md text-sm text-teal-600/60 dark:text-cream-300/60">
          Your prediction history will appear here once you make your first prediction.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div
          key={item.request_id}
          className="border border-cream-300 p-4 dark:border-teal-700"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <p className="text-sm text-teal-800 dark:text-cream-100">
                {truncate(item.question)}
              </p>
              <p className="mt-1 font-mono text-xs text-teal-600/60 dark:text-cream-300/60">
                {item.request_id.slice(0, 8)} &middot; {formatTimestamp(item.timestamp)}
              </p>
            </div>
            <div className="flex-shrink-0 text-right">
              {item.prediction !== null ? (
                <span className="font-mono text-lg text-teal-800 dark:text-cream-100">
                  {formatPercentage(item.prediction)}
                </span>
              ) : (
                <span className="font-mono text-sm text-muted-red">
                  FAILED
                </span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
