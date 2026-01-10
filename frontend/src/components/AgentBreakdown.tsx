import type { AgentPrediction } from '../types/api';
import { formatPercentage, formatCost } from '../utils/format';

interface AgentBreakdownProps {
  predictions: AgentPrediction[];
}

export function AgentBreakdown({ predictions }: AgentBreakdownProps) {
  if (predictions.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="font-mono text-xs text-teal-600/60 dark:text-cream-300/60">
        AGENT PREDICTIONS
      </div>
      <div className="space-y-2">
        {predictions.map((pred) => (
          <div
            key={pred.miner_uid}
            className="flex items-center justify-between border border-cream-300 px-4 py-3 dark:border-teal-700"
          >
            <div className="flex items-center gap-3 font-mono text-xs">
              <span className="text-teal-600/60 dark:text-cream-300/60">
                RANK {pred.rank + 1}
              </span>
              <span className="text-teal-800 dark:text-cream-100">
                UID {pred.miner_uid}
              </span>
            </div>
            <div className="flex items-center gap-4 font-mono text-xs">
              <span className="text-teal-600/40 dark:text-cream-300/40">
                {formatCost(pred.cost)}
              </span>
              <span className="text-teal-800 dark:text-cream-100">
                {formatPercentage(pred.prediction)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
