import { useState, type FormEvent } from 'react';
import { useAgents } from '../hooks/useAgents';
import { usePrediction } from '../hooks/usePrediction';
import { useHealth } from '../hooks/useHealth';
import type { PredictionMode } from '../types/api';
import { getDefaultResolutionDate } from '../utils/format';
import { CategorySelect } from './CategorySelect';
import { ModeSelector } from './ModeSelector';
import { LoadingOverlay } from './LoadingOverlay';
import { ResultDisplay } from './ResultDisplay';
import { ErrorMessage } from './ErrorMessage';
import { Tooltip } from './Tooltip';
import { DateInput } from './DateInput';

export function PredictionForm() {
  const [question, setQuestion] = useState('');
  const [resolutionCriteria, setResolutionCriteria] = useState('');
  const [resolutionDate, setResolutionDate] = useState<string>(getDefaultResolutionDate());
  const [categories, setCategories] = useState<string[]>([]);
  const [mode, setMode] = useState<PredictionMode>('champion');
  const [selectedMinerUid, setSelectedMinerUid] = useState<number | null>(null);

  const { agents, loading: agentsLoading } = useAgents();
  const { submit, result, loading, error, elapsed, reset } = usePrediction();
  const { health } = useHealth();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await submit(
      mode,
      {
        question: question.trim(),
        resolution_criteria: resolutionCriteria.trim(),
        resolution_date: resolutionDate || undefined,
        categories,
      },
      selectedMinerUid ?? undefined
    );
  };

  const isValid =
    question.trim() &&
    resolutionCriteria.trim() &&
    (mode !== 'selected' || selectedMinerUid !== null);

  const handleReset = () => {
    reset();
    setQuestion('');
    setResolutionCriteria('');
    setResolutionDate(getDefaultResolutionDate());
    setCategories([]);
    setMode('champion');
    setSelectedMinerUid(null);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="border-b border-cream-300 pb-6 dark:border-teal-700">
        <h1 className="font-mono text-2xl tracking-tight text-teal-800 dark:text-cream-100">
          FORECAST
        </h1>
        <p className="mt-2 text-sm text-teal-600/60 dark:text-cream-300/60">
          Submit a question for AI-powered probability prediction
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Question */}
        <div className="space-y-3">
          <label htmlFor="question" className="heading-caps text-teal-600/60 dark:text-cream-300/60">
            Question <span className="text-muted-red">*</span>
            <Tooltip content="Must be a binary yes/no question. Keep it short and specific for best results." />
          </label>
          <input
            type="text"
            id="question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Will Bitcoin reach $100,000 by end of 2025?"
            disabled={loading}
            className="w-full border border-cream-300 bg-transparent px-4 py-3 text-teal-800 placeholder:text-teal-600/40 dark:border-teal-700 dark:text-cream-100 dark:placeholder:text-cream-300/40"
          />
        </div>

        {/* Resolution Criteria */}
        <div className="space-y-3">
          <label htmlFor="criteria" className="heading-caps text-teal-600/60 dark:text-cream-300/60">
            Resolution Criteria <span className="text-muted-red">*</span>
            <Tooltip content="Additional context to remove ambiguity. Specify how the question should be resolved, such as which sources to use or what counts as success." />
          </label>
          <textarea
            id="criteria"
            value={resolutionCriteria}
            onChange={(e) => setResolutionCriteria(e.target.value)}
            placeholder="This question resolves YES if Bitcoin's price reaches or exceeds $100,000 USD on any major exchange before December 31, 2025."
            rows={3}
            disabled={loading}
            className="w-full border border-cream-300 bg-transparent px-4 py-3 text-teal-800 placeholder:text-teal-600/40 dark:border-teal-700 dark:text-cream-100 dark:placeholder:text-cream-300/40"
          />
        </div>

        {/* Resolution Date */}
        <div className="space-y-3">
          <label htmlFor="date" className="heading-caps text-teal-600/60 dark:text-cream-300/60">
            Resolution Date
            <Tooltip content="Optional. The date when this question should be resolved. Most agents do not use this value for their predictions. Formats: YYYY-MM-DD or DD.MM.YYYY" />
          </label>
          <DateInput
            id="date"
            value={resolutionDate}
            onChange={setResolutionDate}
            disabled={loading}
            className="w-full border border-cream-300 bg-transparent px-4 py-3 text-teal-800 dark:border-teal-700 dark:text-cream-100 dark:placeholder:text-cream-300/40"
          />
        </div>

        {/* Categories */}
        <CategorySelect value={categories} onChange={setCategories} />

        {/* Mode Selector */}
        <ModeSelector
          mode={mode}
          onModeChange={setMode}
          selectedMinerUid={selectedMinerUid}
          onMinerUidChange={setSelectedMinerUid}
          agents={agents}
          agentsLoading={agentsLoading}
        />

        {/* Submit Button */}
        <Tooltip
          block
          content={
            health
              ? `${health.requests_remaining} of ${health.requests_limit} predictions remaining today`
              : 'Loading quota...'
          }
        >
          <button
            type="submit"
            disabled={loading || !isValid}
            className="btn btn-primary w-full disabled:cursor-not-allowed disabled:opacity-40"
          >
            {loading ? 'PROCESSING...' : 'GET PREDICTION'}
          </button>
        </Tooltip>
      </form>

      {/* Loading Overlay */}
      {loading && <LoadingOverlay elapsed={elapsed} />}

      {/* Error */}
      {error && <ErrorMessage error={error} onDismiss={reset} />}

      {/* Result */}
      {result && !error && (
        <div className="space-y-6">
          <ResultDisplay result={result} mode={mode} />
          <button onClick={handleReset} className="btn btn-secondary w-full">
            NEW PREDICTION
          </button>
        </div>
      )}
    </div>
  );
}
