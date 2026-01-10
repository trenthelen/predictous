import { Tooltip } from './Tooltip';

const CATEGORIES = [
  'Sports',
  'Games',
  'Crypto',
  'Politics',
  'Culture',
  'Geopolitics',
  'Economy',
  'Finance',
  'Stocks',
] as const;

interface CategorySelectProps {
  value: string[];
  onChange: (categories: string[]) => void;
}

export function CategorySelect({ value, onChange }: CategorySelectProps) {
  const toggleCategory = (category: string) => {
    if (value.includes(category)) {
      onChange(value.filter((c) => c !== category));
    } else {
      onChange([...value, category]);
    }
  };

  return (
    <div className="space-y-3">
      <label className="heading-caps text-teal-600/60 dark:text-cream-300/60">
        Categories
        <Tooltip content="Optional. Select relevant categories to help some agents improve their precision and efficiency." />
      </label>
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((category) => (
          <button
            key={category}
            type="button"
            onClick={() => toggleCategory(category)}
            className={`border px-3 py-1.5 font-mono text-xs transition-colors ${
              value.includes(category)
                ? 'border-teal-600 bg-teal-600 text-cream-100 dark:border-cream-200 dark:bg-cream-200 dark:text-teal-900'
                : 'border-cream-300 text-teal-600/80 hover:border-teal-600 hover:text-teal-800 dark:border-teal-700 dark:text-cream-300/80 dark:hover:border-cream-300 dark:hover:text-cream-100'
            }`}
          >
            {category.toUpperCase()}
          </button>
        ))}
      </div>
    </div>
  );
}
