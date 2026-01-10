import type { PredictionMode, AgentInfo } from '../types/api';

const MODES: { value: PredictionMode; label: string; description: string }[] = [
  { value: 'champion', label: 'Champion', description: 'Top-ranked agent' },
  { value: 'council', label: 'Council', description: 'Average of top 3' },
  { value: 'selected', label: 'Selected', description: 'Choose an agent' },
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
    <div className="space-y-3">
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
        Prediction Mode
      </label>
      <div className="flex flex-wrap gap-2">
        {MODES.map(({ value, label, description }) => (
          <button
            key={value}
            type="button"
            onClick={() => onModeChange(value)}
            className={`rounded-lg border px-4 py-2 text-left transition-colors ${
              mode === value
                ? 'border-primary-500 bg-primary-50 text-primary-700 dark:border-primary-400 dark:bg-primary-900/20 dark:text-primary-300'
                : 'border-gray-300 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800'
            }`}
          >
            <div className="font-medium">{label}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">{description}</div>
          </button>
        ))}
      </div>

      {mode === 'selected' && (
        <div className="mt-3">
          <select
            value={selectedMinerUid ?? ''}
            onChange={(e) => onMinerUidChange(e.target.value ? Number(e.target.value) : null)}
            disabled={agentsLoading}
            className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:border-transparent focus:ring-2 focus:ring-primary-500 disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
          >
            <option value="">Select an agent...</option>
            {agents.map((agent) => (
              <option key={agent.miner_uid} value={agent.miner_uid}>
                Rank {agent.rank + 1}: UID {agent.miner_uid}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
