import { ThemeToggle } from './ThemeToggle';
import { HealthStatus } from './HealthStatus';
import { Logo } from './Logo';
import type { Tab } from '../types/app';

interface HeaderProps {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

export function Header({ activeTab, onTabChange }: HeaderProps) {
  return (
    <header className="border-b border-cream-300 dark:border-teal-700">
      <div className="mx-auto max-w-4xl px-6">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <Logo className="h-6 w-6 text-teal-600 dark:text-cream-200" />
            <span className="font-mono text-sm tracking-wider text-teal-800 dark:text-cream-100">
              PREDICTOUS
            </span>
          </div>

          {/* Navigation */}
          <nav className="flex items-center gap-6">
            {(['predict', 'batch', 'history', 'stats'] as const).map((tab) => (
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
