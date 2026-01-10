import { ThemeToggle } from './ThemeToggle';
import { HealthStatus } from './HealthStatus';

interface HeaderProps {
  activeTab: 'predict' | 'history' | 'stats';
  onTabChange: (tab: 'predict' | 'history' | 'stats') => void;
}

export function Header({ activeTab, onTabChange }: HeaderProps) {
  return (
    <header className="border-b border-cream-300 dark:border-teal-700">
      <div className="mx-auto max-w-4xl px-6">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <svg className="h-6 w-6 text-teal-600 dark:text-cream-200" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="12" cy="12" r="3" />
              <path d="M12 2v4m0 12v4M2 12h4m12 0h4" />
              <path d="M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" />
            </svg>
            <span className="font-mono text-sm tracking-wider text-teal-800 dark:text-cream-100">
              PREDICTOUS
            </span>
          </div>

          {/* Navigation */}
          <nav className="flex items-center gap-6">
            {(['predict', 'history', 'stats'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => onTabChange(tab)}
                className={`font-mono text-xs tracking-wider transition-colors ${
                  activeTab === tab
                    ? 'text-teal-800 dark:text-cream-100'
                    : 'text-teal-600/60 hover:text-teal-800 dark:text-cream-300/60 dark:hover:text-cream-100'
                }`}
              >
                {tab.toUpperCase()}
              </button>
            ))}
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-6">
            <HealthStatus />
            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  );
}
