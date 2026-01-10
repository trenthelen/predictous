import { ProgressBar } from './ProgressBar';

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
              <svg className="h-12 w-12 text-teal-600 dark:text-cream-200" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="3" />
                <path d="M12 2v4m0 12v4M2 12h4m12 0h4" />
                <path d="M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" />
              </svg>
            </div>
            <h2 className="font-mono text-lg tracking-wider text-teal-800 dark:text-cream-100">
              GENERATING PREDICTION
            </h2>
            <p className="mt-2 text-sm text-teal-600/60 dark:text-cream-300/60">
              Please wait while our agents analyze your question
            </p>
          </div>
          <ProgressBar elapsed={elapsed} />
        </div>
      </div>
    </div>
  );
}
