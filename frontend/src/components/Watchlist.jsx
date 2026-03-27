import { Link } from 'react-router-dom';

import { formatCurrency, formatPercent } from '../lib/formatters';

export function Watchlist({ items = [], currentSymbol = '' }) {
  return (
    <div className="rounded-[1.35rem] border border-white/10 bg-[#111827]/92 p-4 shadow-[0_20px_36px_rgba(2,6,23,0.28)] backdrop-blur-xl">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#9CA3AF]">Watchlist</div>
          <div className="mt-1 font-display text-lg font-semibold text-white">Market Movers</div>
        </div>
        <div className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[11px] text-[#9CA3AF]">
          {items.length} symbols
        </div>
      </div>

      <div className="mt-4 space-y-2">
        {items.length ? (
          items.map((item) => {
            const active = item.symbol === currentSymbol;
            const positive = Number(item.changePct || 0) >= 0;

            return (
              <Link
                key={item.symbol}
                to={`/stocks/${item.symbol}`}
                className={`flex items-center justify-between gap-3 rounded-[1rem] border px-3 py-3 transition duration-200 ${
                  active
                    ? 'border-[#3B82F6]/35 bg-[#3B82F6]/12'
                    : 'border-white/8 bg-white/[0.03] hover:border-white/18 hover:bg-white/[0.06]'
                }`}
              >
                <div className="min-w-0">
                  <div className="font-display text-sm font-semibold text-white">{item.symbol}</div>
                  <div className="truncate text-xs text-[#9CA3AF]">{item.companyName}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-white">{formatCurrency(item.price)}</div>
                  <div className={`text-xs font-semibold ${positive ? 'text-[#22C55E]' : 'text-[#EF4444]'}`}>
                    {formatPercent(item.changePct)}
                  </div>
                </div>
              </Link>
            );
          })
        ) : (
          <div className="rounded-[1rem] border border-white/8 bg-white/[0.03] px-3 py-5 text-center text-sm text-[#9CA3AF]">
            Watchlist data is not available.
          </div>
        )}
      </div>
    </div>
  );
}
