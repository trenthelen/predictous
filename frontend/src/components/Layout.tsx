import type { ReactNode } from 'react';
import { Header } from './Header';

interface LayoutProps {
  children: ReactNode;
  activeTab: 'predict' | 'history' | 'stats';
  onTabChange: (tab: 'predict' | 'history' | 'stats') => void;
}

export function Layout({ children, activeTab, onTabChange }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Header activeTab={activeTab} onTabChange={onTabChange} />
      <main className="mx-auto max-w-4xl px-4 py-8">{children}</main>
      <footer className="border-t border-gray-200 bg-white py-6 dark:border-gray-800 dark:bg-gray-900">
        <div className="mx-auto max-w-4xl px-4 text-center text-sm text-gray-500 dark:text-gray-500">
          Powered by{' '}
          <a
            href="https://numinouslabs.io/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 hover:underline dark:text-primary-400"
          >
            Numinous
          </a>
        </div>
      </footer>
    </div>
  );
}
