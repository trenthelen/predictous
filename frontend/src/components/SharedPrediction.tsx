import { useState, useEffect } from 'react';
import Markdown from 'react-markdown';
import type { PredictionDetail } from '../types/api';
import { fetchPredictionDetail, ApiError } from '../api/client';
import { Logo } from './Logo';

interface SharedPredictionProps {
  requestId: string;
}

function ProbabilityGauge({ value }: { value: number }) {
  const percentage = value * 100;
  const radius = 70;
  const strokeWidth = 7;
  const cx = 100;
  const cy = 80;
  const valueAngle = Math.PI * (1 - value);
  const arcLength = value * Math.PI * radius;

  const describeArc = (startA: number, endA: number) => {
    const startX = cx + radius * Math.cos(startA);
    const startY = cy - radius * Math.sin(startA);
    const endX = cx + radius * Math.cos(endA);
    const endY = cy - radius * Math.sin(endA);
    const largeArc = Math.abs(endA - startA) > Math.PI ? 1 : 0;
    return `M ${startX} ${startY} A ${radius} ${radius} 0 ${largeArc} 1 ${endX} ${endY}`;
  };

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 90" className="w-full max-w-[220px]">
        <style>{`
          @keyframes drawArc {
            to { stroke-dashoffset: 0; }
          }
          @keyframes subtlePulse {
            0%, 97%, 100% { transform: scale(1); }
            98.5% { transform: scale(1.02); }
          }
        `}</style>
        {/* Background arc */}
        <path
          d={describeArc(Math.PI, 0)}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          className="text-cream-300 dark:text-teal-700"
        />
        {/* Value arc */}
        {value > 0 && (
          <path
            d={describeArc(Math.PI, valueAngle)}
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            className="text-teal-600 dark:text-cream-200"
            style={{
              strokeDasharray: arcLength,
              strokeDashoffset: arcLength,
              animation: 'drawArc 1s ease-out forwards',
            }}
          />
        )}
      </svg>
      {/* Percentage */}
      <div className="flex items-baseline">
        <span
          className="font-mono text-4xl text-teal-800 dark:text-cream-100 sm:text-5xl"
          style={{ animation: 'subtlePulse 10s ease-in-out infinite' }}
        >
          {percentage.toFixed(1)}
        </span>
        <span className="ml-1 font-mono text-xl text-teal-600/60 dark:text-cream-300/60">
          %
        </span>
      </div>
    </div>
  );
}

function formatDate(timestamp: string): string {
  return new Date(timestamp).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export function SharedPrediction({ requestId }: SharedPredictionProps) {
  const [detail, setDetail] = useState<PredictionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reasoningOpen, setReasoningOpen] = useState(false);

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

  const goToMain = () => {
    window.location.href = '/';
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-cream-100 dark:bg-teal-900">
        <div className="font-mono text-sm text-teal-600/60 dark:text-cream-300/60">
          Loading...
        </div>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-cream-100 dark:bg-teal-900">
        <div className="font-mono text-lg text-muted-red">{error}</div>
        <button
          onClick={goToMain}
          className="mt-8 font-mono text-sm text-teal-600 hover:text-teal-800 dark:text-cream-300 dark:hover:text-cream-100"
        >
          Go to Predictous
        </button>
      </div>
    );
  }

  const successfulPredictions = detail.agent_predictions.filter(
    (p) => p.status === 'success' && p.reasoning
  );

  return (
    <div className="flex min-h-screen flex-col bg-cream-100 dark:bg-teal-900">
      {/* Header - top left */}
      <header className="px-6 py-6">
        <div className="mx-auto max-w-2xl">
          <button
            onClick={goToMain}
            className="flex items-center gap-3 transition-opacity hover:opacity-70"
          >
            <Logo className="h-8 w-8 text-teal-600 dark:text-cream-200" />
            <div>
              <div className="font-mono text-sm tracking-wider text-teal-800 dark:text-cream-100">
                PREDICTOUS
              </div>
              <div className="text-xs text-teal-600/60 dark:text-cream-300/60">
                AI Probability Engine
              </div>
            </div>
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="flex flex-1 flex-col px-6 py-4">
        <div className="mx-auto w-full max-w-2xl">
          {/* Prediction area */}
          <div className="border border-cream-300 p-5 dark:border-teal-700 sm:p-6">
            {/* Question */}
            <h1 className="text-center text-lg leading-relaxed text-teal-800 dark:text-cream-100 sm:text-xl">
              {detail.question}
            </h1>

            {/* Gauge */}
            {detail.prediction !== null && (
              <div className="mt-5 flex justify-center">
                <ProbabilityGauge value={detail.prediction} />
              </div>
            )}

            {/* Date */}
            <div className="mt-4 text-center">
              <span className="font-mono text-xs text-teal-600/50 dark:text-cream-300/50">
                {formatDate(detail.timestamp)}
              </span>
            </div>

            {/* CTA - inside card */}
            <div className="mt-6 border-t border-cream-300 pt-5 text-center dark:border-teal-700">
              <button
                onClick={goToMain}
                className="font-mono text-sm text-teal-600 transition-colors hover:text-teal-800 dark:text-cream-300 dark:hover:text-cream-100"
              >
                Get your own prediction →
              </button>
            </div>
          </div>

          {/* Reasoning */}
          {successfulPredictions.length > 0 && (
            <div className="mt-3 border border-cream-300 dark:border-teal-700">
              <button
                onClick={() => setReasoningOpen(!reasoningOpen)}
                className="flex w-full items-center justify-between px-5 py-3 transition-colors hover:bg-cream-200/50 dark:hover:bg-teal-800/50"
              >
                <span className="font-mono text-xs tracking-wider text-teal-600/60 dark:text-cream-300/60">
                  REASONING
                </span>
                <span className="font-mono text-xs text-teal-600/60 dark:text-cream-300/60">
                  {reasoningOpen ? '−' : '+'}
                </span>
              </button>

              {reasoningOpen && (
                <div className="border-t border-cream-300 p-5 dark:border-teal-700">
                  <div className="space-y-5">
                    {successfulPredictions.map((pred, index) => (
                      <div key={index}>
                        {successfulPredictions.length > 1 && (
                          <div className="mb-2 font-mono text-xs text-teal-600/40 dark:text-cream-300/40">
                            AGENT {index + 1}
                          </div>
                        )}
                        <div className="prose prose-sm dark:prose-invert max-w-none text-teal-700 dark:text-cream-200">
                          <Markdown>{pred.reasoning}</Markdown>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
