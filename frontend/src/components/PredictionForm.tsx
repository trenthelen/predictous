import { useState, type FormEvent } from 'react';
import { useAgents } from '../hooks/useAgents';
import { usePrediction } from '../hooks/usePrediction';
import type { PredictionMode } from '../types/api';
import { getDefaultResolutionDate, formatDateForInput, formatDateFromInput } from '../utils/format';
import { CategorySelect } from './CategorySelect';
import { ModeSelector } from './ModeSelector';
import { ProgressBar } from './ProgressBar';
import { ResultDisplay } from './ResultDisplay';
import { ErrorMessage } from './ErrorMessage';

export function PredictionForm() {
  const [question, setQuestion] = useState('');
  const [resolutionCriteria, setResolutionCriteria] = useState('');
  const [resolutionDate, setResolutionDate] = useState<string>(getDefaultResolutionDate());
  const [categories, setCategories] = useState<string[]>([]);
  const [mode, setMode] = useState<PredictionMode>('champion');
  const [selectedMinerUid, setSelectedMinerUid] = useState<number | null>(null);

  const { agents, loading: agentsLoading } = useAgents();
  const { submit, result, loading, error, elapsed, reset } = usePrediction();

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
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Question */}
        <div>
          <label
            htmlFor="question"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Question <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Will Bitcoin reach $100,000 by end of 2025?"
            disabled={loading}
            className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder-gray-400 focus:border-transparent focus:ring-2 focus:ring-primary-500 disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
          />
        </div>

        {/* Resolution Criteria */}
        <div>
          <label
            htmlFor="criteria"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Resolution Criteria <span className="text-red-500">*</span>
          </label>
          <textarea
            id="criteria"
            value={resolutionCriteria}
            onChange={(e) => setResolutionCriteria(e.target.value)}
            placeholder="This question resolves YES if Bitcoin's price reaches or exceeds $100,000 USD on any major exchange before December 31, 2025."
            rows={3}
            disabled={loading}
            className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder-gray-400 focus:border-transparent focus:ring-2 focus:ring-primary-500 disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
          />
        </div>

        {/* Resolution Date */}
        <div>
          <label
            htmlFor="date"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Resolution Date <span className="font-normal text-gray-500">(optional)</span>
          </label>
          <input
            type="datetime-local"
            id="date"
            value={formatDateForInput(resolutionDate)}
            onChange={(e) => setResolutionDate(formatDateFromInput(e.target.value))}
            disabled={loading}
            className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:border-transparent focus:ring-2 focus:ring-primary-500 disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
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
        <button
          type="submit"
          disabled={loading || !isValid}
          className="w-full rounded-lg bg-primary-600 px-6 py-3 font-medium text-white transition-colors hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? 'Processing...' : 'Get Prediction'}
        </button>
      </form>

      {/* Progress Bar */}
      {loading && <ProgressBar elapsed={elapsed} />}

      {/* Error */}
      {error && <ErrorMessage error={error} onDismiss={reset} />}

      {/* Result */}
      {result && !error && (
        <div className="space-y-4">
          <ResultDisplay result={result} mode={mode} />
          <button
            onClick={handleReset}
            className="w-full rounded-lg border border-gray-300 bg-white px-6 py-2 text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            New Prediction
          </button>
        </div>
      )}
    </div>
  );
}
