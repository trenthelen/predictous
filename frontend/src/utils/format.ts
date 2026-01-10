export function formatPercentage(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (mins > 0) {
    return `${mins}m ${secs}s`;
  }
  return `${secs}s`;
}

export function formatCost(cost: number): string {
  return `$${cost.toFixed(4)}`;
}

export function getDefaultResolutionDate(): string {
  const date = new Date();
  date.setFullYear(date.getFullYear() + 1);
  return date.toISOString();
}

export function formatDateForInput(isoString: string): string {
  // Convert ISO string to datetime-local format (YYYY-MM-DDTHH:mm)
  if (!isoString) return '';
  return isoString.slice(0, 16);
}

export function formatDateFromInput(localString: string): string {
  // Convert datetime-local to ISO format with Z suffix
  if (!localString) return '';
  const date = new Date(localString);
  if (isNaN(date.getTime())) return '';
  return date.toISOString();
}

export function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function truncate(text: string, maxLength = 80): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}
