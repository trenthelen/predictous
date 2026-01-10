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
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
        Categories <span className="font-normal text-gray-500">(optional)</span>
      </label>
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((category) => (
          <button
            key={category}
            type="button"
            onClick={() => toggleCategory(category)}
            className={`rounded-full px-3 py-1 text-sm transition-colors ${
              value.includes(category)
                ? 'bg-primary-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
            }`}
          >
            {category}
          </button>
        ))}
      </div>
    </div>
  );
}
