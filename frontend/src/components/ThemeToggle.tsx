import { useTheme, type Theme } from '../hooks/useTheme';

const SunIcon = () => (
  <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="5" />
    <path d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
  </svg>
);

const MoonIcon = () => (
  <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
  </svg>
);

const AutoIcon = () => (
  <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="2" y="3" width="20" height="14" rx="2" />
    <path d="M8 21h8m-4-4v4" />
  </svg>
);

const THEMES: { value: Theme; icon: React.ReactNode; label: string }[] = [
  { value: 'light', icon: <SunIcon />, label: 'Light' },
  { value: 'dark', icon: <MoonIcon />, label: 'Dark' },
  { value: 'system', icon: <AutoIcon />, label: 'System' },
];

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex items-center border border-cream-300 dark:border-teal-700">
      {THEMES.map(({ value, icon, label }) => (
        <button
          key={value}
          onClick={() => setTheme(value)}
          className={`p-2 transition-colors ${
            theme === value
              ? 'bg-teal-600 text-cream-100 dark:bg-cream-200 dark:text-teal-900'
              : 'text-teal-600/60 hover:text-teal-800 dark:text-cream-300/60 dark:hover:text-cream-100'
          }`}
          title={label}
        >
          {icon}
        </button>
      ))}
    </div>
  );
}
