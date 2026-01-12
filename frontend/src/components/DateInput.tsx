import { useState, useEffect, useRef } from 'react';

interface DateInputProps {
  value: string; // ISO string
  onChange: (isoString: string) => void;
  disabled?: boolean;
  className?: string;
  id?: string;
}

function parseDate(input: string): Date | null {
  if (!input.trim()) return null;

  // Try parsing YYYY-MM-DD format (ISO)
  const isoMatch = input.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
  if (isoMatch) {
    const [, year, month, day] = isoMatch;
    const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    if (!isNaN(date.getTime())) return date;
  }

  // Try parsing DD.MM.YYYY format (EU with dots only to avoid US ambiguity)
  const euMatch = input.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})$/);
  if (euMatch) {
    const [, day, month, year] = euMatch;
    const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    if (!isNaN(date.getTime())) return date;
  }

  return null;
}

function formatDisplayDate(isoString: string): string {
  if (!isoString) return '';
  return isoString.slice(0, 10); // YYYY-MM-DD
}

// Format date to YYYY-MM-DD without timezone conversion
function toLocalDateString(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// Create ISO string preserving the local date (noon UTC to avoid date shift)
function toISOStringPreserveDate(date: Date): string {
  const dateStr = toLocalDateString(date);
  return `${dateStr}T12:00:00.000Z`;
}

export function DateInput({ value, onChange, disabled, className, id }: DateInputProps) {
  const [inputValue, setInputValue] = useState(() => formatDisplayDate(value));
  const [isInvalid, setIsInvalid] = useState(false);
  const datePickerRef = useRef<HTMLInputElement>(null);

  // Sync input value when external value changes
  useEffect(() => {
    setInputValue(formatDisplayDate(value));
    setIsInvalid(false);
  }, [value]);

  const handleBlur = () => {
    if (!inputValue.trim()) {
      onChange('');
      setIsInvalid(false);
      return;
    }

    const parsed = parseDate(inputValue);
    if (parsed) {
      const iso = toISOStringPreserveDate(parsed);
      onChange(iso);
      setInputValue(toLocalDateString(parsed));
      setIsInvalid(false);
    } else {
      setIsInvalid(true);
    }
  };

  const handleDatePick = (e: React.ChangeEvent<HTMLInputElement>) => {
    const dateValue = e.target.value;
    if (dateValue) {
      const [year, month, day] = dateValue.split('-').map(Number);
      const date = new Date(year, month - 1, day);
      if (!isNaN(date.getTime())) {
        const iso = toISOStringPreserveDate(date);
        onChange(iso);
        setInputValue(toLocalDateString(date));
        setIsInvalid(false);
      }
    }
  };

  const openDatePicker = () => {
    datePickerRef.current?.showPicker();
  };

  return (
    <div className="relative">
      <input
        type="text"
        id={id}
        value={inputValue}
        onChange={(e) => {
          setInputValue(e.target.value);
          setIsInvalid(false);
        }}
        onBlur={handleBlur}
        placeholder="YYYY-MM-DD"
        disabled={disabled}
        className={`${className} pr-10 ${isInvalid ? 'border-muted-red!' : ''}`}
      />
      <input
        ref={datePickerRef}
        type="date"
        value={formatDisplayDate(value)}
        onChange={handleDatePick}
        disabled={disabled}
        className="absolute inset-0 opacity-0 pointer-events-none"
        tabIndex={-1}
      />
      <button
        type="button"
        onClick={openDatePicker}
        disabled={disabled}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-teal-600/60 hover:text-teal-800 dark:text-cream-300/60 dark:hover:text-cream-100 disabled:opacity-40"
        aria-label="Open calendar"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
          <path fillRule="evenodd" d="M5.75 2a.75.75 0 0 1 .75.75V4h7V2.75a.75.75 0 0 1 1.5 0V4h.25A2.75 2.75 0 0 1 18 6.75v8.5A2.75 2.75 0 0 1 15.25 18H4.75A2.75 2.75 0 0 1 2 15.25v-8.5A2.75 2.75 0 0 1 4.75 4H5V2.75A.75.75 0 0 1 5.75 2Zm-1 5.5c-.69 0-1.25.56-1.25 1.25v6.5c0 .69.56 1.25 1.25 1.25h10.5c.69 0 1.25-.56 1.25-1.25v-6.5c0-.69-.56-1.25-1.25-1.25H4.75Z" clipRule="evenodd" />
        </svg>
      </button>
    </div>
  );
}
