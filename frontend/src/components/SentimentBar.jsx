import clsx from 'clsx';

function sentimentColor(value) {
  if (value > 0.1) return 'bg-positive';
  if (value < -0.1) return 'bg-negative';
  return 'bg-neutral';
}

function sentimentLabel(value) {
  if (value > 0.1) return 'Positive';
  if (value < -0.1) return 'Negative';
  return 'Neutral';
}

export function SentimentBar({ value = 0, compact = false }) {
  const clamped = Math.max(-1, Math.min(1, Number(value || 0)));
  const width = ((clamped + 1) / 2) * 100;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs font-medium text-muted">
        <span>{sentimentLabel(clamped)}</span>
        <span className={clsx('font-display text-sm', clamped > 0 ? 'text-positive' : clamped < 0 ? 'text-negative' : 'text-neutral')}>
          {clamped.toFixed(2)}
        </span>
      </div>
      <div className={clsx('overflow-hidden rounded-full bg-white/10', compact ? 'h-2' : 'h-3')}>
        <div
          className={clsx('h-full rounded-full transition-all', sentimentColor(clamped))}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}
