import { formatTime } from '../utils/format';

const ESTIMATED_SECONDS = 150;

interface ProgressBarProps {
  elapsed: number;
}

export function ProgressBar({ elapsed }: ProgressBarProps) {
  const percentage = Math.min((elapsed / ESTIMATED_SECONDS) * 100, 95);
  const remaining = Math.max(ESTIMATED_SECONDS - elapsed, 0);

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
        <span>Processing prediction...</span>
        <span>~{formatTime(remaining)} remaining</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
        <div
          className="h-full bg-primary-500 transition-all duration-1000"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
