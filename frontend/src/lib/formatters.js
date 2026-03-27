export function formatCurrency(value, currency = 'INR', compact = false) {
  const numeric = Number(value ?? 0);
  if (!Number.isFinite(numeric)) return '-';

  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    maximumFractionDigits: compact ? 1 : 2,
    notation: compact ? 'compact' : 'standard',
  }).format(numeric);
}

export function formatNumber(value, digits = 2) {
  const numeric = Number(value ?? 0);
  if (!Number.isFinite(numeric)) return '-';

  return new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: digits,
  }).format(numeric);
}

export function formatPercent(value, digits = 2) {
  const numeric = Number(value ?? 0);
  if (!Number.isFinite(numeric)) return '-';
  return `${numeric >= 0 ? '+' : ''}${numeric.toFixed(digits)}%`;
}

export function formatDate(value) {
  if (!value) return '-';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);

  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(date);
}

export function formatDateTime(value) {
  if (!value) return '-';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);

  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export function formatCompactNumber(value) {
  const numeric = Number(value ?? 0);
  if (!Number.isFinite(numeric)) return '-';

  return new Intl.NumberFormat('en-IN', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(numeric);
}

export function toTitleCase(value) {
  if (!value) return '-';
  return String(value)
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase());
}
