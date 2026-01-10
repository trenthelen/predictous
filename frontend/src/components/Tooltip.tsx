import { useState, useRef, useEffect, type ReactNode } from 'react';

interface TooltipProps {
  content: string;
  children?: ReactNode;
  block?: boolean;
}

export function Tooltip({ content, children, block }: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const [position, setPosition] = useState<'top' | 'bottom'>('top');
  const tooltipRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (visible && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      const spaceAbove = rect.top;
      const spaceBelow = window.innerHeight - rect.bottom;
      setPosition(spaceAbove > 100 || spaceAbove > spaceBelow ? 'top' : 'bottom');
    }
  }, [visible]);

  const Wrapper = block ? 'div' : 'span';

  return (
    <Wrapper
      ref={triggerRef}
      className={`relative ${block ? 'block' : 'inline-flex items-center'}`}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children ?? (
        <span className="ml-1 flex h-3 w-3 cursor-help items-center justify-center rounded-full border border-teal-600/30 text-[8px] text-teal-600/50 dark:border-cream-300/30 dark:text-cream-300/50">
          ?
        </span>
      )}
      {visible && (
        <div
          ref={tooltipRef}
          className={`absolute left-1/2 z-50 w-64 -translate-x-1/2 px-3 py-2 text-xs font-normal normal-case tracking-normal ${
            position === 'top' ? 'bottom-full mb-2' : 'top-full mt-2'
          }`}
        >
          <div className="rounded border border-cream-300 bg-cream-100 text-teal-700 shadow-sm dark:border-teal-600 dark:bg-teal-800 dark:text-cream-200">
            <div className="p-2 leading-relaxed">{content}</div>
          </div>
        </div>
      )}
    </Wrapper>
  );
}
