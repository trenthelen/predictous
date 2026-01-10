import type { PredictResponse, PredictionMode } from '../types/api';
import { formatPercentage, formatCost } from '../utils/format';
import { AgentBreakdown } from './AgentBreakdown';
import { FailureDisplay } from './FailureDisplay';

interface ResultDisplayProps {
  result: PredictResponse;
  mode: PredictionMode;
}

export function ResultDisplay({ result, mode }: ResultDisplayProps) {
  if (result.status === 'error' && result.prediction === null) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center dark:border-red-900 dark:bg-red-900/20">
        <p className="text-red-800 dark:text-red-200">{result.error || 'Prediction failed'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
      {/* Main probability display */}
      {result.prediction !== null && (
        <div className="text-center">
          <div className="text-6xl font-bold text-primary-600 dark:text-primary-400">
            {formatPercentage(result.prediction)}
          </div>
          <div className="mt-2 text-gray-600 dark:text-gray-400">Probability</div>
        </div>
      )}

      {/* Council mode breakdown */}
      {mode === 'council' && result.agent_predictions.length > 0 && (
        <AgentBreakdown predictions={result.agent_predictions} />
      )}

      {/* Failures */}
      {result.failures.length > 0 && <FailureDisplay failures={result.failures} />}

      {/* Cost info */}
      <div className="border-t border-gray-200 pt-4 text-center text-sm text-gray-500 dark:border-gray-700 dark:text-gray-500">
        Total cost: {formatCost(result.total_cost)}
      </div>
    </div>
  );
}
