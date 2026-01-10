import { formatTime } from '../utils/format';

const ESTIMATED_SECONDS = 150;

interface ProgressBarProps {
  elapsed: number;
}

export function ProgressBar({ elapsed }: ProgressBarProps) {
  const percentage = Math.min((elapsed / ESTIMATED_SECONDS) * 100, 95);
  const remaining = Math.max(ESTIMATED_SECONDS - elapsed, 0);

  return (
    <div className="border border-cream-300 p-6 dark:border-teal-700">
      <div className="flex items-center justify-between font-mono text-xs">
        <span className="text-teal-600/60 dark:text-cream-300/60">PROCESSING</span>
        <span className="text-teal-800 dark:text-cream-100">~{formatTime(remaining)}</span>
      </div>
      <div className="mt-4 h-1 bg-cream-300 dark:bg-teal-700">
        <div
          className="h-full bg-teal-600 transition-all duration-1000 dark:bg-cream-200"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="mt-3 font-mono text-xs text-teal-600/40 dark:text-cream-300/40">
        ELAPSED: {formatTime(elapsed)}
      </div>
    </div>
  );
}
