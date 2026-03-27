import clsx from 'clsx';
import { ArrowRight, TrendingDown, TrendingUp } from 'lucide-react';
import { Link } from 'react-router-dom';

import { formatCurrency, formatPercent } from '../lib/formatters';
import { SentimentBar } from './SentimentBar';

function badgeClasses(signal) {
  if (signal === 'BUY') return 'bg-positive/10 text-positive border-positive/20';
  if (signal === 'SELL') return 'bg-negative/10 text-negative border-negative/20';
  return 'bg-neutral/10 text-neutral border-neutral/20';
}

export function StockCard({ stock, intent = 'default' }) {
  const positive = stock.changePct >= 0;

  return (
    <Link
      to={`/stocks/${stock.symbol}`}
      className="panel group flex h-full flex-col p-6 transition duration-200 hover:-translate-y-1 hover:shadow-panel"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">{stock.symbol}</div>
          <h3 className="mt-2 font-display text-xl font-bold text-brand">{stock.companyName}</h3>
          <p className="mt-1 text-sm text-muted">{stock.sector}</p>
        </div>
        <div className={clsx('rounded-full border px-3 py-1 text-xs font-semibold', badgeClasses(stock.signal))}>
          {stock.signal}
        </div>
      </div>

      <div className="mt-6 flex items-end justify-between">
        <div>
          <div className="font-display text-3xl font-bold tracking-tight text-brand">
            {formatCurrency(stock.price)}
          </div>
          <div className={`mt-2 inline-flex items-center gap-1 text-sm font-semibold ${positive ? 'text-positive' : 'text-negative'}`}>
            {positive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
            {formatPercent(stock.changePct)}
          </div>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3 text-right">
          <div className="text-xs text-muted">AI Prediction</div>
          <div className="font-display text-lg font-bold text-brand">
            {stock.prediction}
            <span className="ml-2 text-sm text-muted">{Math.round(stock.confidence || 0)}%</span>
          </div>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3">
        <div className="rounded-2xl bg-slate-50 p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-muted">RSI</div>
          <div className="mt-2 font-display text-xl font-bold text-brand">{stock.rsi.toFixed(1)}</div>
        </div>
        <div className="rounded-2xl bg-slate-50 p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-muted">MACD</div>
          <div className="mt-2 font-display text-xl font-bold text-brand">{stock.macd.toFixed(2)}</div>
        </div>
      </div>

      <div className="mt-5">
        <SentimentBar value={stock.sentimentScore} />
      </div>

      <div className="mt-6 flex items-center justify-between border-t border-line pt-4 text-sm font-semibold text-brand">
        <span>{intent === 'buy' ? 'Open buy thesis' : intent === 'sell' ? 'Inspect risk setup' : 'View full analysis'}</span>
        <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
      </div>
    </Link>
  );
}
