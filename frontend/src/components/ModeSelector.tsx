import type { PredictionMode, AgentInfo } from '../types/api';
import { Tooltip } from './Tooltip';

const MODES: { value: PredictionMode; label: string; desc: string }[] = [
  { value: 'champion', label: 'CHAMPION', desc: 'Top agent' },
  { value: 'council', label: 'COUNCIL', desc: 'Top 3 averaged' },
  { value: 'selected', label: 'SELECTED', desc: 'Choose agent' },
];

interface ModeSelectorProps {
  mode: PredictionMode;
  onModeChange: (mode: PredictionMode) => void;
  selectedMinerUid: number | null;
  onMinerUidChange: (uid: number | null) => void;
  agents: AgentInfo[];
  agentsLoading: boolean;
}

export function ModeSelector({
  mode,
  onModeChange,
  selectedMinerUid,
  onMinerUidChange,
  agents,
  agentsLoading,
}: ModeSelectorProps) {
  return (
    <div className="space-y-4">
      <label className="heading-caps text-teal-600/60 dark:text-cream-300/60">
        Mode
        <Tooltip content="Choose which AI agents generate your prediction. Champion uses the top-ranked agent, Council averages the top 3, or select a specific agent." />
      </label>

      <div className="grid grid-cols-3 gap-3">
        {MODES.map(({ value, label, desc }) => (
          <button
            key={value}
            type="button"
            onClick={() => onModeChange(value)}
            className={`border p-4 text-left transition-colors ${
              mode === value
                ? 'border-teal-600 dark:border-cream-200'
                : 'border-cream-300 hover:border-teal-600/50 dark:border-teal-700 dark:hover:border-cream-300/50'
            }`}
          >
            <div className="font-mono text-xs tracking-wider text-teal-800 dark:text-cream-100">
              {label}
            </div>
            <div className="mt-1 text-xs text-teal-600/60 dark:text-cream-300/60">
              {desc}
            </div>
          </button>
        ))}
      </div>

      {mode === 'selected' && (
        <select
          value={selectedMinerUid ?? ''}
          onChange={(e) => onMinerUidChange(e.target.value ? Number(e.target.value) : null)}
          disabled={agentsLoading}
          className="w-full border border-cream-300 bg-transparent px-4 py-3 font-mono text-sm text-teal-800 dark:border-teal-700 dark:text-cream-100"
        >
          <option value="" className="bg-cream-100 dark:bg-teal-900">Select agent...</option>
          {agents.map((agent) => (
            <option key={agent.miner_uid} value={agent.miner_uid} className="bg-cream-100 dark:bg-teal-900">
              Rank {agent.rank + 1}: UID {agent.miner_uid}
            </option>
          ))}
        </select>
      )}
    </div>
  );
}
