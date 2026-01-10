import { ApiError, getErrorMessage } from '../api/client';

interface ErrorMessageProps {
  error: ApiError;
  onDismiss?: () => void;
}

export function ErrorMessage({ error, onDismiss }: ErrorMessageProps) {
  const message = getErrorMessage(error);

  return (
    <div className="border border-muted-red/30 bg-muted-red/5 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="font-mono text-xs text-muted-red">ERROR</div>
          <p className="mt-2 text-sm text-teal-800 dark:text-cream-200">{message}</p>
          {error.errorCode && (
            <p className="mt-2 font-mono text-xs text-teal-600/60 dark:text-cream-300/60">
              CODE: {error.errorCode}
            </p>
          )}
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="font-mono text-xs text-teal-600/60 hover:text-teal-800 dark:text-cream-300/60 dark:hover:text-cream-100"
          >
            DISMISS
          </button>
        )}
      </div>
    </div>
  );
}
