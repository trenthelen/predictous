import type { PredictResponse, PredictionMode } from '../types/api';
import { formatPercentage, formatCost } from '../utils/format';
import { AgentBreakdown } from './AgentBreakdown';
import { FailureDisplay } from './FailureDisplay';
import { Reasoning } from './Reasoning';

interface ResultDisplayProps {
  result: PredictResponse;
  mode: PredictionMode;
}

export function ResultDisplay({ result, mode }: ResultDisplayProps) {
  if (result.status === 'error' && result.prediction === null) {
    return (
      <div className="border border-muted-red/30 bg-muted-red/5 p-6 text-center">
        <p className="text-sm text-teal-800 dark:text-cream-200">
          {result.error || 'Prediction failed'}
        </p>
      </div>
    );
  }

  return (
    <div className="border border-cream-300 dark:border-teal-700">
      {/* Main probability display */}
      {result.prediction !== null && (
        <div className="border-b border-cream-300 p-8 text-center dark:border-teal-700">
          <div className="font-mono text-xs text-teal-600/60 dark:text-cream-300/60">
            PROBABILITY
          </div>
          <div className="mt-2 font-mono text-5xl tracking-tight text-teal-800 dark:text-cream-100">
            {formatPercentage(result.prediction)}
          </div>
        </div>
      )}

      {/* Council mode breakdown */}
      {mode === 'council' && result.agent_predictions.length > 0 && (
        <div className="border-b border-cream-300 p-6 dark:border-teal-700">
          <AgentBreakdown predictions={result.agent_predictions} />
        </div>
      )}

      {/* Reasoning (foldable) */}
      {result.agent_predictions.length > 0 && (
        <div className="border-b border-cream-300 dark:border-teal-700">
          <Reasoning predictions={result.agent_predictions} />
        </div>
      )}

      {/* Failures */}
      {result.failures.length > 0 && (
        <div className="border-b border-cream-300 p-6 dark:border-teal-700">
          <FailureDisplay failures={result.failures} />
        </div>
      )}

      {/* Cost info */}
      <div className="flex items-center justify-between p-4 font-mono text-xs">
        <span className="text-teal-600/60 dark:text-cream-300/60">COST</span>
        <span className="text-teal-800 dark:text-cream-100">{formatCost(result.total_cost)}</span>
      </div>
    </div>
  );
}
