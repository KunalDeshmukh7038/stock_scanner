import { Activity, BrainCircuit, ChartCandlestick, Gauge, Newspaper } from 'lucide-react';

import { formatCompactNumber, formatCurrency, formatNumber, formatPercent } from '../lib/formatters';
import { Watchlist } from './Watchlist';

function DetailMetric({ label, value, icon: Icon }) {
  return (
    <div className="rounded-[1rem] border border-white/8 bg-white/[0.03] p-3">
      <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-[#9CA3AF]">
        {Icon ? <Icon className="h-3.5 w-3.5" /> : null}
        {label}
      </div>
      <div className="mt-2 text-sm font-semibold text-white">{value}</div>
    </div>
  );
}

export function RightPanel({ detail, currentPrice, watchlistItems = [] }) {
  const positive = Number(detail.changePct || 0) >= 0;

  return (
    <div className="grid gap-4 xl:grid-rows-[auto_auto_1fr]">
      <Watchlist items={watchlistItems} currentSymbol={detail.symbol} />

      <div className="rounded-[1.35rem] border border-white/10 bg-[#111827]/92 p-4 shadow-[0_20px_36px_rgba(2,6,23,0.28)] backdrop-blur-xl">
        <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#9CA3AF]">Details</div>
        <div className="mt-2 flex items-start justify-between gap-4">
          <div>
            <div className="font-display text-xl font-semibold text-white">{detail.symbol}</div>
            <div className="mt-1 text-sm text-[#9CA3AF]">{detail.companyName}</div>
          </div>
          <div className={`rounded-full px-3 py-1 text-xs font-semibold ${positive ? 'bg-[#22C55E]/12 text-[#22C55E]' : 'bg-[#EF4444]/12 text-[#EF4444]'}`}>
            {detail.signal}
          </div>
        </div>

        <div className="mt-4 rounded-[1rem] border border-white/8 bg-black/10 p-4">
          <div className="font-display text-3xl font-bold text-white">{formatCurrency(currentPrice)}</div>
          <div className={`mt-2 text-sm font-semibold ${positive ? 'text-[#22C55E]' : 'text-[#EF4444]'}`}>
            {formatPercent(detail.changePct)}
          </div>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
          <DetailMetric label="Prediction" value={`${detail.prediction} | ${Math.round(detail.confidence || 0)}%`} icon={BrainCircuit} />
          <DetailMetric label="Market Cap" value={formatCompactNumber(detail.marketCap)} icon={ChartCandlestick} />
          <DetailMetric label="RSI" value={formatNumber(detail.rsi, 1)} icon={Gauge} />
          <DetailMetric label="Sentiment" value={formatNumber(detail.sentimentScore, 2)} icon={Newspaper} />
          <DetailMetric label="P/E" value={formatNumber(detail.pe, 2)} icon={Activity} />
        </div>
      </div>
    </div>
  );
}
