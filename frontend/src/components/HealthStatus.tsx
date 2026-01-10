import { useHealth } from '../hooks/useHealth';
import { Tooltip } from './Tooltip';

export function HealthStatus() {
  const { health, loading } = useHealth();

  if (loading || !health) {
    return (
      <span className="font-mono text-xs text-teal-600/40 dark:text-cream-300/40">
        ...
      </span>
    );
  }

  return (
    <Tooltip content="Your prediction allowance over a rolling 24-hour window.">
      <div className="flex cursor-help items-center gap-2 font-mono text-xs">
        <span className="text-teal-600/60 dark:text-cream-300/60">QUOTA</span>
        <span className="text-teal-800 dark:text-cream-100">
          {health.requests_remaining}/{health.requests_limit}
        </span>
        <span className="flex h-2.5 w-2.5 items-center justify-center rounded-full border border-teal-600/30 text-[7px] text-teal-600/50 dark:border-cream-300/30 dark:text-cream-300/50">
          ?
        </span>
      </div>
    </Tooltip>
  );
}
