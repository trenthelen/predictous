import { useState } from 'react';
import type { AgentPrediction } from '../types/api';

interface ReasoningProps {
  predictions: AgentPrediction[];
}

export function Reasoning({ predictions }: ReasoningProps) {
  const [expanded, setExpanded] = useState(false);

  // Filter predictions that have reasoning
  const withReasoning = predictions.filter((p) => p.reasoning);
  if (withReasoning.length === 0) return null;

  return (
    <div className="border-t border-gray-200 pt-4 dark:border-gray-700">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between text-left text-sm font-medium text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white"
      >
        <span>Reasoning</span>
        <svg
          className={`h-5 w-5 transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className="mt-3 space-y-4">
          {withReasoning.map((pred) => (
            <div key={pred.miner_uid} className="rounded-lg bg-gray-50 p-4 dark:bg-gray-800">
              {withReasoning.length > 1 && (
                <div className="mb-2 text-xs font-medium text-gray-500 dark:text-gray-400">
                  Rank {pred.rank + 1} (UID {pred.miner_uid})
                </div>
              )}
              <p className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300">
                {pred.reasoning}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
