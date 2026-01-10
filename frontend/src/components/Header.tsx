import { useState } from 'react';
import { ThemeToggle } from './ThemeToggle';
import { HealthStatus } from './HealthStatus';
import { Logo } from './Logo';
import type { Tab } from '../types/app';

interface HeaderProps {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

export function Header({ activeTab, onTabChange }: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleTabChange = (tab: Tab) => {
    onTabChange(tab);
    setMobileMenuOpen(false);
  };

  return (
    <header className="border-b border-cream-300 dark:border-teal-700">
      <div className="mx-auto max-w-4xl px-4 sm:px-6">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2 sm:gap-3">
            <Logo className="h-6 w-6 text-teal-600 dark:text-cream-200" />
            <span className="font-mono text-sm tracking-wider text-teal-800 dark:text-cream-100">
              PREDICTOUS
            </span>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden items-center gap-6 md:flex">
            {(['predict', 'history', 'batch', 'stats'] as const).map((tab) => (
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

          {/* Desktop Right side */}
          <div className="hidden items-center gap-6 md:flex">
            <HealthStatus />
            <ThemeToggle />
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="flex items-center justify-center p-2 text-teal-600 dark:text-cream-200 md:hidden"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? (
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="border-t border-cream-200 py-4 dark:border-teal-700 md:hidden">
            <nav className="flex flex-col gap-3">
              {(['predict', 'history', 'batch', 'stats'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => handleTabChange(tab)}
                  className={`py-2 text-left font-mono text-xs tracking-wider transition-colors ${
                    activeTab === tab
                      ? 'text-teal-800 dark:text-cream-100'
                      : 'text-teal-600/60 hover:text-teal-800 dark:text-cream-300/60 dark:hover:text-cream-100'
                  }`}
                >
                  {tab.toUpperCase()}
                </button>
              ))}
            </nav>
            <div className="mt-4 flex items-center justify-between border-t border-cream-200 pt-4 dark:border-teal-700">
              <HealthStatus />
              <ThemeToggle />
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
