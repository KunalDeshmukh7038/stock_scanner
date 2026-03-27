export function Gauge({ value = 0, min = 0, max = 100, label, color = '#22C55E' }) {
  const safeValue = Math.max(min, Math.min(max, Number(value || 0)));
  const ratio = (safeValue - min) / (max - min);
  const angle = -90 + ratio * 180;
  const x = 50 + 38 * Math.cos((Math.PI * angle) / 180);
  const y = 50 + 38 * Math.sin((Math.PI * angle) / 180);

  return (
    <div className="panel-muted p-5">
      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">{label}</div>
      <div className="mt-4 flex items-center justify-center">
        <svg viewBox="0 0 100 60" className="h-36 w-full max-w-[220px]">
          <path d="M10 50 A40 40 0 0 1 90 50" fill="none" stroke="#243041" strokeWidth="10" strokeLinecap="round" />
          <path
            d={`M50 50 L${x} ${y}`}
            fill="none"
            stroke={color}
            strokeWidth="4"
            strokeLinecap="round"
          />
          <circle cx="50" cy="50" r="5" fill={color} />
        </svg>
      </div>
      <div className="mt-2 text-center font-display text-3xl font-bold text-white">{safeValue.toFixed(1)}</div>
    </div>
  );
}
