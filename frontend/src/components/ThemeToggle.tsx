import { useTheme, type Theme } from '../hooks/useTheme';

const THEMES: { value: Theme; icon: string }[] = [
  { value: 'light', icon: '/' },
  { value: 'dark', icon: '\\' },
  { value: 'system', icon: 'A' },
];

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex items-center border border-cream-300 dark:border-teal-700">
      {THEMES.map(({ value, icon }) => (
        <button
          key={value}
          onClick={() => setTheme(value)}
          className={`px-2 py-1 font-mono text-xs transition-colors ${
            theme === value
              ? 'bg-teal-600 text-cream-100 dark:bg-cream-200 dark:text-teal-900'
              : 'text-teal-600/60 hover:text-teal-800 dark:text-cream-300/60 dark:hover:text-cream-100'
          }`}
          title={value.charAt(0).toUpperCase() + value.slice(1)}
        >
          {icon}
        </button>
      ))}
    </div>
  );
}
