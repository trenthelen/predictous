import { ThemeToggle } from './ThemeToggle';
import { HealthStatus } from './HealthStatus';

interface HeaderProps {
  activeTab: 'predict' | 'history' | 'stats';
  onTabChange: (tab: 'predict' | 'history' | 'stats') => void;
}

export function Header({ activeTab, onTabChange }: HeaderProps) {
  return (
    <header className="border-b border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
      <div className="mx-auto max-w-4xl px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold text-gray-900 dark:text-white">Predictous</span>
          </div>

          {/* Navigation */}
          <nav className="flex items-center gap-1">
            <button
              onClick={() => onTabChange('predict')}
              className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                activeTab === 'predict'
                  ? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-white'
                  : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'
              }`}
            >
              Predict
            </button>
            <button
              onClick={() => onTabChange('history')}
              className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                activeTab === 'history'
                  ? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-white'
                  : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'
              }`}
            >
              History
            </button>
            <button
              onClick={() => onTabChange('stats')}
              className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                activeTab === 'stats'
                  ? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-white'
                  : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'
              }`}
            >
              Statistics
            </button>
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-4">
            <HealthStatus />
            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  );
}
