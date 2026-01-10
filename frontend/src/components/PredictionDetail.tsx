import { useState, useEffect } from 'react';
import type { PredictionDetail as PredictionDetailType } from '../types/api';
import { fetchPredictionDetail, ApiError } from '../api/client';
import { formatPercentage, formatTimestamp, formatCost } from '../utils/format';

interface PredictionDetailProps {
  requestId: string;
  onBack: () => void;
}

export function PredictionDetail({ requestId, onBack }: PredictionDetailProps) {
  const [detail, setDetail] = useState<PredictionDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchPredictionDetail(requestId);
        setDetail(data);
      } catch (e) {
        if (e instanceof ApiError && e.status === 404) {
          setError('Prediction not found');
        } else {
          setError('Failed to load prediction');
        }
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [requestId]);

  const getShareUrl = () => {
    return `${window.location.origin}/predictions/${requestId}`;
  };

  const handleShare = async () => {
    const shareUrl = getShareUrl();
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for browsers without clipboard API
      const input = document.createElement('input');
      input.value = shareUrl;
      document.body.appendChild(input);
      input.select();
      document.execCommand('copy');
      document.body.removeChild(input);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="font-mono text-sm text-teal-600/60 dark:text-cream-300/60">
          Loading...
        </div>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="font-mono text-sm text-muted-red">{error}</div>
        <button
          onClick={onBack}
          className="mt-6 font-mono text-xs text-teal-600 hover:text-teal-800 dark:text-cream-300 dark:hover:text-cream-100"
        >
          &larr; Back
        </button>
      </div>
    );
  }

  const successfulPredictions = detail.agent_predictions.filter(
    (p) => p.status === 'success' && p.prediction !== null
  );

  return (
    <div className="space-y-6">
      {/* Header with back and share */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="font-mono text-xs text-teal-600 hover:text-teal-800 dark:text-cream-300 dark:hover:text-cream-100"
        >
          &larr; Back
        </button>
        <button
          onClick={handleShare}
          className="flex items-center gap-2 border border-cream-300 px-3 py-1.5 font-mono text-xs text-teal-600 transition-colors hover:bg-cream-200 dark:border-teal-700 dark:text-cream-300 dark:hover:bg-teal-800"
        >
          {copied ? 'Copied!' : 'Share'}
        </button>
      </div>

      {/* Main prediction result */}
      <div className="border border-cream-300 p-6 dark:border-teal-700">
        <div className="mb-4 font-mono text-xs text-teal-600/60 dark:text-cream-300/60">
          {detail.request_id.slice(0, 8)} &middot; {formatTimestamp(detail.timestamp)}
        </div>

        <h1 className="text-lg text-teal-800 dark:text-cream-100">{detail.question}</h1>

        {detail.prediction !== null && (
          <div className="mt-6 text-center">
            <div className="font-mono text-4xl text-teal-800 dark:text-cream-100">
              {formatPercentage(detail.prediction)}
            </div>
            <div className="mt-1 font-mono text-xs text-teal-600/60 dark:text-cream-300/60">
              AVERAGE FORECAST
            </div>
          </div>
        )}
      </div>

      {/* Resolution criteria */}
      <div className="border border-cream-300 p-4 dark:border-teal-700">
        <div className="mb-2 font-mono text-xs text-teal-600/60 dark:text-cream-300/60">
          RESOLUTION CRITERIA
        </div>
        <p className="text-sm text-teal-700 dark:text-cream-200">
          {detail.resolution_criteria}
        </p>
        {detail.resolution_date && (
          <div className="mt-3 font-mono text-xs text-teal-600/60 dark:text-cream-300/60">
            Resolves: {new Date(detail.resolution_date).toLocaleDateString()}
          </div>
        )}
      </div>

      {/* Agent predictions */}
      {successfulPredictions.length > 0 && (
        <div className="space-y-3">
          <div className="font-mono text-xs text-teal-600/60 dark:text-cream-300/60">
            AGENT PREDICTIONS ({successfulPredictions.length})
          </div>
          <div className="space-y-2">
            {successfulPredictions.map((pred, index) => (
              <div
                key={index}
                className="border border-cream-300 dark:border-teal-700"
              >
                <div className="flex items-center justify-between px-4 py-3">
                  <div className="font-mono text-xs text-teal-600/60 dark:text-cream-300/60">
                    AGENT {index + 1}
                  </div>
                  <div className="flex items-center gap-4 font-mono text-xs">
                    <span className="text-teal-600/40 dark:text-cream-300/40">
                      {formatCost(pred.cost)}
                    </span>
                    <span className="text-teal-800 dark:text-cream-100">
                      {pred.prediction !== null
                        ? formatPercentage(pred.prediction)
                        : '-'}
                    </span>
                  </div>
                </div>
                {pred.reasoning && (
                  <div className="border-t border-cream-300 px-4 py-3 dark:border-teal-700">
                    <p className="whitespace-pre-wrap text-sm leading-relaxed text-teal-700 dark:text-cream-200">
                      {pred.reasoning}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
