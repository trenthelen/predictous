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
    <div>
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-cream-200/50 dark:hover:bg-teal-800/50"
      >
        <span className="font-mono text-xs text-teal-600/60 dark:text-cream-300/60">
          REASONING
        </span>
        <span className="font-mono text-xs text-teal-600/60 dark:text-cream-300/60">
          {expanded ? '[-]' : '[+]'}
        </span>
      </button>

      {expanded && (
        <div className="space-y-4 border-t border-cream-300 p-6 dark:border-teal-700">
          {withReasoning.map((pred) => (
            <div key={pred.miner_uid}>
              {withReasoning.length > 1 && (
                <div className="mb-2 font-mono text-xs text-teal-600/60 dark:text-cream-300/60">
                  RANK {pred.rank + 1} / UID {pred.miner_uid}
                </div>
              )}
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-teal-700 dark:text-cream-200">
                {pred.reasoning}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
