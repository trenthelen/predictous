import type { AgentPrediction } from '../types/api';
import { formatPercentage, formatCost } from '../utils/format';

interface AgentBreakdownProps {
  predictions: AgentPrediction[];
}

export function AgentBreakdown({ predictions }: AgentBreakdownProps) {
  if (predictions.length === 0) return null;

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
        Individual Agent Predictions
      </h3>
      <div className="space-y-2">
        {predictions.map((pred) => (
          <div
            key={pred.miner_uid}
            className="flex items-center justify-between rounded-lg bg-gray-50 p-3 dark:bg-gray-800"
          >
            <div className="flex items-center gap-3">
              <span className="rounded bg-gray-200 px-2 py-0.5 text-xs font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-400">
                Rank {pred.rank + 1}
              </span>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                UID {pred.miner_uid}
              </span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-xs text-gray-500">{formatCost(pred.cost)}</span>
              <span className="font-semibold text-gray-900 dark:text-white">
                {formatPercentage(pred.prediction)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
