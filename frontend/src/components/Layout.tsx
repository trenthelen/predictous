import type { ReactNode } from 'react';
import { Header } from './Header';
import type { Tab } from '../types/app';

interface LayoutProps {
  children: ReactNode;
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

export function Layout({ children, activeTab, onTabChange }: LayoutProps) {
  return (
    <div className="min-h-screen bg-cream-100 text-teal-800 dark:bg-teal-900 dark:text-cream-200">
      {/* Grid overlay - vertical lines aligned with content container */}
      <div className="pointer-events-none fixed inset-0 flex justify-center">
        <div className="relative w-full max-w-4xl">
          <div className="absolute left-0 top-0 bottom-0 w-px bg-cream-300 opacity-50 dark:bg-teal-700" />
          <div className="absolute right-0 top-0 bottom-0 w-px bg-cream-300 opacity-50 dark:bg-teal-700" />
        </div>
      </div>

      <div className="relative">
        <Header activeTab={activeTab} onTabChange={onTabChange} />

        {/* Main content area */}
        <main className="mx-auto max-w-4xl px-6 py-12">
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t border-cream-300 dark:border-teal-700">
          <div className="mx-auto max-w-4xl px-6 py-6 flex justify-between items-center">
            <span className="font-mono text-xs text-teal-600/60 dark:text-cream-300/60">
              POWERED BY{' '}
              <a
                href="https://numinouslabs.io/"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-teal-800 dark:hover:text-cream-100"
              >
                NUMINOUS
              </a>
            </span>
            <span className="font-mono text-xs text-teal-600/60 dark:text-cream-300/60">
              BUILDING THE FUTURE OF FORECASTING
            </span>
          </div>
        </footer>
      </div>
    </div>
  );
}
