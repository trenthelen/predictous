import { ProgressBar } from './ProgressBar';
import { Logo } from './Logo';

interface LoadingOverlayProps {
  elapsed: number;
}

export function LoadingOverlay({ elapsed }: LoadingOverlayProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-cream-100/95 dark:bg-teal-900/95">
      <div className="w-full max-w-md px-6">
        <div className="border border-cream-300 bg-cream-50 p-8 dark:border-teal-700 dark:bg-teal-800">
          <div className="mb-6 text-center">
            <div className="mb-4 inline-block animate-pulse">
              <Logo className="h-12 w-12 text-teal-600 dark:text-cream-200" />
            </div>
            <h2 className="font-mono text-lg tracking-wider text-teal-800 dark:text-cream-100">
              GENERATING PREDICTION
            </h2>
            <p className="mt-2 text-sm text-teal-600/60 dark:text-cream-300/60">
              Please bear with us — this is a thorough process. Our agents are researching current information, analyzing relevant data, and thoughtfully generating their prediction.
            </p>
          </div>
          <ProgressBar elapsed={elapsed} />
        </div>
      </div>
    </div>
  );
}
