import type { ReactNode } from 'react';
import { Header } from './Header';

interface LayoutProps {
  children: ReactNode;
  activeTab: 'predict' | 'history' | 'stats';
  onTabChange: (tab: 'predict' | 'history' | 'stats') => void;
}

export function Layout({ children, activeTab, onTabChange }: LayoutProps) {
  return (
    <div className="min-h-screen bg-cream-100 text-teal-800 dark:bg-teal-900 dark:text-cream-200">
      {/* Grid overlay for visual structure */}
      <div className="fixed inset-0 pointer-events-none">
        {/* Vertical lines */}
        <div className="absolute left-[20%] top-0 bottom-0 w-px bg-cream-300 dark:bg-teal-700 opacity-50" />
        <div className="absolute right-[20%] top-0 bottom-0 w-px bg-cream-300 dark:bg-teal-700 opacity-50" />
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
              POWERED BY NUMINOUS
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
