import { formatDateTime, formatNumber, formatPercent } from '../lib/formatters';

export function MarketTickerBar({ items = [], meta = {} }) {
  const liveClass = meta.isLive
    ? 'border-positive/25 bg-positive/10 text-positive'
    : 'border-amber-400/25 bg-amber-400/10 text-amber-300';

  return (
    <div className="overflow-hidden rounded-[1.7rem] border border-white/10 bg-[#0f172a]/92 shadow-[0_28px_60px_rgba(2,6,23,0.38)] backdrop-blur-2xl">
      <div className="flex flex-col gap-3 border-b border-white/10 bg-gradient-to-r from-white/[0.04] via-transparent to-white/[0.02] px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <div className={`rounded-full border px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] ${liveClass}`}>
              {meta.isLive ? 'LIVE' : 'Fallback'}
            </div>
            <div className="text-sm text-muted">
              Source: <span className="font-semibold text-white">{meta.source || 'Fallback'}</span>
            </div>
          </div>
          {meta.message ? <div className="mt-2 text-sm text-muted">{meta.message}</div> : null}
        </div>
        <div className="text-sm text-muted">
          Last updated: <span className="font-semibold text-white">{formatDateTime(meta.lastUpdated)}</span>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="sticky top-0 z-10 bg-[#0f172a]/95 backdrop-blur">
            <tr className="border-b border-white/10">
              {['Index name', 'Last traded', 'Day change', 'High', 'Low', 'Open', 'Prev. Close'].map((heading) => (
                <th key={heading} className="whitespace-nowrap border-b border-white/10 px-5 py-4 text-left text-[0.82rem] font-semibold uppercase tracking-[0.16em] text-muted">
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 bg-surface/90">
            {items.length ? items.map((item, index) => {
              const positive = item.changePct >= 0;

              return (
                <tr
                  key={item.symbol}
                  className={`${index % 2 === 0 ? 'bg-white/[0.01]' : 'bg-white/[0.035]'} transition duration-200 hover:bg-white/[0.07]`}
                >
                  <td className="px-5 py-5">
                    <div className="font-display text-[1.05rem] font-bold text-white">{item.name}</div>
                    <div className="mt-1 text-sm text-muted">{formatDateTime(item.timestamp)}</div>
                  </td>
                  <td className="px-5 py-5 font-medium text-white">{formatNumber(item.value, 2)}</td>
                  <td className={`px-5 py-5 text-[1.02rem] font-semibold ${positive ? 'text-positive' : 'text-negative'}`}>
                    {formatNumber(item.change, 2)} ({formatPercent(item.changePct)})
                  </td>
                  <td className="px-5 py-5 text-[1.02rem] text-ink">{formatNumber(item.high, 2)}</td>
                  <td className="px-5 py-5 text-[1.02rem] text-ink">{formatNumber(item.low, 2)}</td>
                  <td className="px-5 py-5 text-[1.02rem] text-ink">{formatNumber(item.open, 2)}</td>
                  <td className="px-5 py-5 text-[1.02rem] text-ink">{formatNumber(item.prevClose, 2)}</td>
                </tr>
              );
            }) : (
              <tr>
                <td colSpan={7} className="px-5 py-10 text-center text-sm text-muted">
                  {meta.message || 'No market data is available right now. Please check the backend source and refresh.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
