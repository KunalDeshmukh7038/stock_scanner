import { useDeferredValue, useEffect, useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Activity, ArrowDownRight, ArrowUpRight, BrainCircuit, Building2, CandlestickChart, Newspaper, Radar, SearchCode, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

import { TableSkeleton } from './LoadingSkeleton';
import { MarketTickerBar } from './MarketTickerBar';
import { api, getMarketSocketUrl } from '../lib/api';
import { formatCurrency, formatNumber, formatPercent } from '../lib/formatters';
import { normalizeMarketResponse } from '../lib/normalize';

function InsightCard({ icon: Icon, label, value, helper, tone = 'default' }) {
  const tones = {
    default: 'border-white/10 bg-white/[0.04] text-white',
    positive: 'border-positive/20 bg-positive/10 text-positive',
    negative: 'border-negative/20 bg-negative/10 text-negative',
    neutral: 'border-amber-400/20 bg-amber-400/10 text-amber-300',
  };

  return (
    <div className={`rounded-[1.4rem] border p-5 shadow-[0_18px_38px_rgba(2,6,23,0.24)] transition duration-300 hover:-translate-y-1 hover:shadow-[0_22px_48px_rgba(2,6,23,0.34)] ${tones[tone]}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.22em] text-muted">{label}</div>
          <div className="mt-3 font-display text-3xl font-bold tracking-tight">{value}</div>
        </div>
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-black/20 shadow-sm">
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <div className="mt-3 text-sm text-muted">{helper}</div>
    </div>
  );
}

function SignalSpotlight({ title, subtitle, items, type, prefetchStock }) {
  const toneClasses =
    type === 'buy'
      ? 'border-positive/20 bg-[linear-gradient(180deg,rgba(34,197,94,0.14),rgba(15,23,42,0.86))]'
      : 'border-negative/20 bg-[linear-gradient(180deg,rgba(239,68,68,0.12),rgba(15,23,42,0.86))]';

  const badgeClasses =
    type === 'buy'
      ? 'bg-positive/15 text-positive'
      : 'bg-negative/15 text-negative';

  return (
    <div className={`rounded-[1.6rem] border p-6 shadow-[0_20px_50px_rgba(2,6,23,0.32)] ${toneClasses}`}>
      <div className="flex items-center justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-[0.28em] text-muted">{title}</div>
          <div className="mt-2 text-sm text-muted">{subtitle}</div>
        </div>
        <div className={`rounded-full px-3 py-1.5 text-xs font-semibold ${badgeClasses}`}>
          {type === 'buy' ? 'Momentum' : 'Risk Radar'}
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {items.length ? (
          items.map((stock) => (
            <Link
              key={stock.symbol}
              to={`/stocks/${stock.symbol}`}
              onMouseEnter={() => prefetchStock(stock.symbol)}
              onFocus={() => prefetchStock(stock.symbol)}
              className="flex items-center justify-between gap-4 rounded-[1.2rem] border border-white/10 bg-black/15 px-4 py-4 transition duration-300 hover:-translate-y-0.5 hover:border-white/20 hover:bg-white/[0.06]"
            >
              <div className="min-w-0">
                <div className="font-display text-lg font-bold text-white">{stock.symbol}</div>
                <div className="truncate text-sm text-muted">{stock.companyName}</div>
              </div>
              <div className="text-right">
                <div className="font-display text-lg font-bold text-white">{stock.prediction}</div>
                <div className={`text-sm font-semibold ${stock.changePct >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                  {formatPercent(stock.changePct)}
                </div>
              </div>
            </Link>
          ))
        ) : (
          <div className="rounded-[1.2rem] border border-dashed border-white/15 bg-black/10 px-4 py-5 text-sm text-muted">
            No matching signals yet for the current filters.
          </div>
        )}
      </div>
    </div>
  );
}

function TinyLine({ values = [], positive = true }) {
  if (!values.length) return null;

  const width = 180;
  const height = 72;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const points = values
    .map((value, index) => {
      const x = (index / Math.max(values.length - 1, 1)) * width;
      const y = height - ((value - min) / (max - min || 1)) * (height - 8) - 4;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-16 w-full">
      <polyline
        points={points}
        fill="none"
        stroke={positive ? '#22C55E' : '#EF4444'}
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function HeroTerminalPreview({ market = [], stocks = [], prefetchStock }) {
  const featured = stocks.slice(0, 6);
  const chartSeed = stocks.slice(0, 18).map((stock, index) => Number(stock.price || 0) + index * 3);
  const watchlist = stocks.slice(0, 5);
  const newsItems = stocks.slice(0, 3);

  return (
    <div className="relative mt-8">
      <div className="pointer-events-none absolute inset-x-[8%] -top-3 h-20 rounded-full bg-[#8b5cf6]/30 blur-[95px]" />
      <div className="pointer-events-none absolute -left-8 top-24 h-32 w-32 rounded-full bg-[#2563eb]/25 blur-[95px]" />
      <div className="pointer-events-none absolute -right-6 bottom-10 h-28 w-28 rounded-full bg-[#ef4444]/20 blur-[85px]" />

      <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(180deg,rgba(8,12,22,0.96),rgba(14,20,34,0.98))] p-3 shadow-[0_35px_90px_rgba(2,6,23,0.5)]">
        <div className="grid gap-3 xl:grid-cols-[46px_minmax(0,1fr)_280px]">
          <div className="hidden rounded-[1.3rem] border border-white/8 bg-white/[0.03] p-2 xl:flex xl:flex-col xl:items-center xl:gap-3">
            {[Radar, SearchCode, CandlestickChart, Activity, BrainCircuit, Newspaper].map((Icon, index) => (
              <div
                key={index}
                className={`flex h-9 w-9 items-center justify-center rounded-xl border ${
                  index === 0
                    ? 'border-[#3B82F6]/40 bg-[#3B82F6]/18 text-white'
                    : 'border-white/8 bg-white/[0.03] text-muted'
                }`}
              >
                <Icon className="h-4 w-4" />
              </div>
            ))}
          </div>

          <div className="grid gap-3">
            <div className="rounded-[1.4rem] border border-white/10 bg-black/20 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-muted">Market Workspace</div>
                  <div className="mt-1 font-display text-lg font-semibold text-white">Live chart preview</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {['1D', '1W', '1M', 'Indicators'].map((item, index) => (
                    <div
                      key={item}
                      className={`rounded-full border px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] ${
                        index === 0
                          ? 'border-[#3B82F6]/40 bg-[#3B82F6]/16 text-white'
                          : 'border-white/10 bg-white/[0.03] text-muted'
                      }`}
                    >
                      {item}
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-5 grid gap-3 xl:grid-cols-[1.25fr_0.75fr]">
                <div className="rounded-[1.2rem] border border-white/8 bg-[radial-gradient(circle_at_top,_rgba(37,99,235,0.14),_transparent_40%),linear-gradient(180deg,rgba(9,14,24,0.96),rgba(11,17,32,0.98))] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="font-display text-xl font-semibold text-white">NIFTY 100 Terminal</div>
                      <div className="mt-1 text-sm text-muted">Cross-market context with AI signal overlay</div>
                    </div>
                    <div className="rounded-full border border-positive/20 bg-positive/12 px-3 py-1 text-xs font-semibold text-positive">
                      LIVE
                    </div>
                  </div>

                  <div className="mt-5 grid gap-3 sm:grid-cols-3">
                    {market.slice(0, 3).map((item) => (
                      <div key={item.symbol} className="rounded-[1rem] border border-white/8 bg-white/[0.03] px-3 py-3">
                        <div className="text-[11px] uppercase tracking-[0.16em] text-muted">{item.name}</div>
                        <div className="mt-2 text-lg font-semibold text-white">{formatNumber(item.value, 2)}</div>
                        <div className={`mt-1 text-xs font-semibold ${Number(item.changePct || 0) >= 0 ? 'text-positive' : 'text-negative'}`}>
                          {formatPercent(item.changePct)}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="mt-6 rounded-[1rem] border border-white/8 bg-black/20 px-3 py-4">
                    <TinyLine values={chartSeed} positive={Number(stocks[0]?.changePct || 0) >= 0} />
                  </div>
                </div>

                <div className="grid gap-3">
                  {featured.slice(0, 4).map((stock) => (
                    <Link
                      key={stock.symbol}
                      to={`/stocks/${stock.symbol}`}
                      onMouseEnter={() => prefetchStock(stock.symbol)}
                      onFocus={() => prefetchStock(stock.symbol)}
                      className="rounded-[1rem] border border-white/8 bg-white/[0.03] px-4 py-3 transition duration-200 hover:border-white/20 hover:bg-white/[0.06]"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <div className="font-display text-sm font-semibold text-white">{stock.symbol}</div>
                          <div className="mt-1 text-xs text-muted">{stock.companyName}</div>
                        </div>
                        <div className={`text-sm font-semibold ${Number(stock.changePct || 0) >= 0 ? 'text-positive' : 'text-negative'}`}>
                          {formatPercent(stock.changePct)}
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid gap-3 xl:grid-cols-2">
              <div className="rounded-[1.2rem] border border-white/8 bg-white/[0.03] p-4">
                <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-muted">Signal Grid</div>
                <div className="mt-4 grid grid-cols-3 gap-2">
                  {featured.slice(0, 6).map((stock) => (
                    <div
                      key={stock.symbol}
                      className={`rounded-[0.95rem] px-3 py-3 text-center text-xs font-semibold ${
                        stock.signal === 'BUY'
                          ? 'bg-positive/14 text-positive'
                          : stock.signal === 'SELL'
                            ? 'bg-negative/14 text-negative'
                            : 'bg-white/[0.04] text-white'
                      }`}
                    >
                      {stock.symbol}
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-[1.2rem] border border-white/8 bg-white/[0.03] p-4">
                <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-muted">AI Headlines</div>
                <div className="mt-4 space-y-3">
                  {newsItems.map((stock) => (
                    <div key={stock.symbol} className="rounded-[0.95rem] border border-white/8 bg-black/15 px-3 py-3">
                      <div className="text-sm font-semibold text-white">{stock.symbol} updates</div>
                      <div className="mt-1 text-xs leading-5 text-muted">
                        {stock.prediction} bias with {Math.round(stock.confidence || 0)}% confidence in the current market structure.
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-[1.4rem] border border-white/10 bg-black/22 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-muted">Main Watchlist</div>
                <div className="mt-1 font-display text-lg font-semibold text-white">Top active names</div>
              </div>
              <div className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[11px] text-muted">
                Real-time
              </div>
            </div>

            <div className="mt-4 space-y-2">
              {watchlist.map((stock) => (
                <Link
                  key={stock.symbol}
                  to={`/stocks/${stock.symbol}`}
                  onMouseEnter={() => prefetchStock(stock.symbol)}
                  onFocus={() => prefetchStock(stock.symbol)}
                  className="flex items-center justify-between gap-3 rounded-[1rem] border border-white/8 bg-white/[0.03] px-3 py-3 transition duration-200 hover:border-white/20 hover:bg-white/[0.06]"
                >
                  <div>
                    <div className="font-display text-sm font-semibold text-white">{stock.symbol}</div>
                    <div className="mt-1 text-xs text-muted">{stock.sector}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-white">{formatCurrency(stock.price)}</div>
                    <div className={`mt-1 text-xs font-semibold ${Number(stock.changePct || 0) >= 0 ? 'text-positive' : 'text-negative'}`}>
                      {formatPercent(stock.changePct)}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function StockScreenerView() {
  const queryClient = useQueryClient();
  const [query, setQuery] = useState('');
  const [sector, setSector] = useState('ALL');
  const [signal, setSignal] = useState('ALL');
  const [minRsi, setMinRsi] = useState('');
  const [maxRsi, setMaxRsi] = useState('');
  const [minSentiment, setMinSentiment] = useState('');
  const [maxSentiment, setMaxSentiment] = useState('');
  const deferredQuery = useDeferredValue(query);

  const bootstrapQuery = useQuery({
    queryKey: ['bootstrap'],
    queryFn: api.getBootstrap,
    retry: 0,
  });

  const stocksFallbackQuery = useQuery({
    queryKey: ['stocks'],
    queryFn: api.getStocks,
    enabled: bootstrapQuery.isError || (bootstrapQuery.isSuccess && !(bootstrapQuery.data?.stocks?.length)),
  });

  const marketFallbackQuery = useQuery({
    queryKey: ['market'],
    queryFn: api.getMarket,
    enabled: bootstrapQuery.isError || (bootstrapQuery.isSuccess && !(bootstrapQuery.data?.market?.items?.length)),
  });

  const bootstrapMarketPayload = bootstrapQuery.data?.market?.items?.length ? bootstrapQuery.data.market : null;
  const fallbackMarketPayload = marketFallbackQuery.data?.items?.length ? marketFallbackQuery.data : null;
  const baseMarketPayload = bootstrapMarketPayload || fallbackMarketPayload || { items: [], meta: {} };
  const [streamMarketPayload, setStreamMarketPayload] = useState(null);

  useEffect(() => {
    setStreamMarketPayload(baseMarketPayload.items.length ? baseMarketPayload : null);
  }, [baseMarketPayload]);

  useEffect(() => {
    const socket = new WebSocket(getMarketSocketUrl());

    socket.onmessage = (event) => {
      try {
        const payload = normalizeMarketResponse(JSON.parse(event.data));
        if (payload.items.length) {
          setStreamMarketPayload(payload);
        }
      } catch (error) {
        console.error('Unable to parse market stream payload', error);
      }
    };

    socket.onerror = () => {
      socket.close();
    };

    return () => {
      socket.close();
    };
  }, []);

  const stocks = bootstrapQuery.data?.stocks?.length ? bootstrapQuery.data.stocks : (stocksFallbackQuery.data || []);
  const marketPayload = streamMarketPayload?.items?.length ? streamMarketPayload : baseMarketPayload;
  const market = marketPayload.items || [];
  const marketMeta = marketPayload.meta || {};
  const isLoading = bootstrapQuery.isLoading || (bootstrapQuery.isError && (stocksFallbackQuery.isLoading || marketFallbackQuery.isLoading));
  const hasData = stocks.length > 0 || market.length > 0;
  const showWarning = bootstrapQuery.isError && hasData;
  const showError = bootstrapQuery.isError && !hasData && !stocksFallbackQuery.isLoading && !marketFallbackQuery.isLoading;
  const sectors = ['ALL', ...new Set(stocks.map((stock) => stock.sector).filter(Boolean))];
  const buySignals = stocks
    .filter((stock) => stock.signal === 'BUY')
    .sort((first, second) => second.confidence - first.confidence)
    .slice(0, 3);
  const sellSignals = stocks
    .filter((stock) => stock.signal === 'SELL')
    .sort((first, second) => second.confidence - first.confidence)
    .slice(0, 3);
  const positiveCount = stocks.filter((stock) => stock.changePct >= 0).length;
  const avgConfidence = stocks.length
    ? stocks.reduce((sum, stock) => sum + Number(stock.confidence || 0), 0) / stocks.length
    : 0;
  const avgSentiment = stocks.length
    ? stocks.reduce((sum, stock) => sum + Number(stock.sentimentScore || 0), 0) / stocks.length
    : 0;

  const filtered = stocks.filter((stock) => {
    const matchesQuery =
      !deferredQuery ||
      stock.symbol.toLowerCase().includes(deferredQuery.toLowerCase()) ||
      stock.companyName.toLowerCase().includes(deferredQuery.toLowerCase());

    const matchesSector = sector === 'ALL' || stock.sector === sector;
    const matchesSignal = signal === 'ALL' || stock.signal === signal;
    const matchesMinRsi = minRsi === '' || stock.rsi >= Number(minRsi);
    const matchesMaxRsi = maxRsi === '' || stock.rsi <= Number(maxRsi);
    const matchesMinSentiment = minSentiment === '' || stock.sentimentScore >= Number(minSentiment);
    const matchesMaxSentiment = maxSentiment === '' || stock.sentimentScore <= Number(maxSentiment);

    return (
      matchesQuery &&
      matchesSector &&
      matchesSignal &&
      matchesMinRsi &&
      matchesMaxRsi &&
      matchesMinSentiment &&
      matchesMaxSentiment
    );
  });

  function prefetchStock(symbol) {
    queryClient.prefetchQuery({
      queryKey: ['stock-detail', symbol],
      queryFn: () => api.getStock(symbol),
      staleTime: 300_000,
    });
  }

  const warmSymbols = useMemo(
    () => [
      ...stocks.filter((stock) => stock.signal === 'BUY').slice(0, 3).map((stock) => stock.symbol),
      ...stocks.filter((stock) => stock.signal === 'SELL').slice(0, 3).map((stock) => stock.symbol),
      ...stocks.slice(0, 4).map((stock) => stock.symbol),
    ]
      .filter((stockSymbol, index, values) => values.indexOf(stockSymbol) === index)
      .slice(0, 8),
    [stocks],
  );

  useEffect(() => {
    if (!stocks.length) return;

    const timer = window.setTimeout(() => {
      warmSymbols.forEach((stockSymbol) => {
        prefetchStock(stockSymbol);
      });
    }, 250);

    return () => window.clearTimeout(timer);
  }, [warmSymbols, stocks]);

  return (
    <div className="space-y-8">
      <section className="relative overflow-hidden rounded-[2.4rem] border border-white/10 bg-[radial-gradient(circle_at_50%_0%,rgba(122,92,255,0.14),transparent_24%),radial-gradient(circle_at_12%_82%,rgba(37,99,235,0.16),transparent_22%),radial-gradient(circle_at_88%_76%,rgba(244,63,94,0.14),transparent_20%),linear-gradient(180deg,rgba(3,5,12,0.98),rgba(8,11,19,1))] px-6 py-8 shadow-[0_40px_110px_rgba(2,6,23,0.56)] sm:px-8 lg:px-10 lg:py-10">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-32 bg-[linear-gradient(180deg,rgba(255,255,255,0.03),transparent)]" />

        <div className="relative mx-auto max-w-[1260px]">
          <div className="flex flex-col items-center text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-highlight">
              <Radar className="h-4 w-4" />
              Trading workspace for NIFTY intelligence
            </div>

            <h1 className="mt-6 max-w-5xl font-display text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-[4.6rem] lg:leading-[0.95]">
              Where your market research becomes a live trading terminal
            </h1>

            <p className="mt-5 max-w-3xl text-base leading-7 text-muted sm:text-lg sm:leading-8">
              Scan NIFTY leaders, track live market structure, and move from sentiment to decision-making in a darker, faster, more professional workspace.
            </p>

            <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
              <div className="rounded-full border border-white/10 bg-white/[0.05] px-5 py-2.5 text-sm font-semibold text-white shadow-[0_10px_24px_rgba(2,6,23,0.26)]">
                99+ tracked stocks
              </div>
              <div className="rounded-full border border-white/10 bg-white/[0.03] px-5 py-2.5 text-sm text-muted">
                Live indices + AI signals
              </div>
              <div className="rounded-full border border-[#3B82F6]/30 bg-[#3B82F6]/12 px-5 py-2.5 text-sm font-semibold text-white">
                Chart-led research flow
              </div>
            </div>
          </div>

          <HeroTerminalPreview market={market} stocks={stocks} prefetchStock={prefetchStock} />

          <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <InsightCard
              icon={Building2}
              label="Coverage"
              value={`${stocks.length || 0}`}
              helper="Tracked NIFTY universe stocks"
            />
            <InsightCard
              icon={ArrowUpRight}
              label="Advancing"
              value={`${positiveCount}`}
              helper="Stocks trading positive today"
              tone="positive"
            />
            <InsightCard
              icon={BrainCircuit}
              label="Avg Confidence"
              value={`${Math.round(avgConfidence)}%`}
              helper="AI conviction across active universe"
              tone="neutral"
            />
            <InsightCard
              icon={ShieldCheck}
              label="Avg Sentiment"
              value={formatNumber(avgSentiment, 2)}
              helper="Mean news and narrative tone"
            />
          </div>

          <div className="mt-6 grid gap-4 xl:grid-cols-2">
            <SignalSpotlight
              title="Top Buy Setup"
              subtitle="High-confidence names with constructive technical posture."
              items={buySignals}
              type="buy"
              prefetchStock={prefetchStock}
            />
            <SignalSpotlight
              title="Top Sell Alert"
              subtitle="Names with weaker momentum and downside pressure."
              items={sellSignals}
              type="sell"
              prefetchStock={prefetchStock}
            />
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-end justify-between gap-4">
          <div>
            <div className="text-sm font-bold uppercase tracking-[0.32em] text-highlight">Live Market</div>
            <h2 className="mt-2 font-display text-2xl font-bold text-white sm:text-3xl">
              NIFTY 50, NIFTY 100, BANKNIFTY, SENSEX, BTC-USD, GOLD and SILVER
            </h2>
            <p className="mt-2 text-sm text-muted">
              Exchange context first, so every screen result sits inside the broader market move.
            </p>
          </div>
          <div className="hidden rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-muted lg:inline-flex">
            Live dashboard overview
          </div>
        </div>
        {isLoading ? <TableSkeleton /> : <MarketTickerBar items={market} meta={marketMeta} />}
        {showWarning ? (
          <div className="rounded-[1.4rem] border border-amber-400/25 bg-amber-400/10 px-4 py-3 text-sm text-amber-300">
            Live bootstrap feed had a problem, so the page is using fallback API requests.
          </div>
        ) : null}
      </section>

      <section className="overflow-hidden rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.12),_transparent_34%),linear-gradient(180deg,rgba(17,24,39,0.98),rgba(15,23,42,0.94))] px-6 py-10 shadow-[0_22px_60px_rgba(2,6,23,0.4)] sm:px-8 lg:px-10">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <div className="text-sm font-bold uppercase tracking-[0.36em] text-highlight">Screener</div>
            <h2 className="mt-4 font-display text-4xl font-bold tracking-tight text-white sm:text-5xl">
              Filter NIFTY 100 stocks like a research terminal
            </h2>
            <p className="mt-4 text-lg leading-8 text-muted">
              Search faster, filter cleaner, and move from market pulse to stock-level conviction in one scroll.
            </p>
          </div>
          <div className="grid gap-3 rounded-[1.75rem] border border-white/10 bg-white/[0.03] p-4 shadow-[0_14px_34px_rgba(2,6,23,0.24)] sm:grid-cols-3 lg:w-[29rem] lg:grid-cols-1">
            <div className="flex items-center gap-3 rounded-[1.2rem] border border-white/5 bg-black/10 px-4 py-3">
              <SearchCode className="h-5 w-5 text-highlight" />
              <div>
                <div className="text-sm font-semibold text-white">Search + sector filters</div>
                <div className="text-xs text-muted">Reduce noise quickly</div>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-[1.2rem] border border-white/5 bg-black/10 px-4 py-3">
              <ArrowUpRight className="h-5 w-5 text-positive" />
              <div>
                <div className="text-sm font-semibold text-white">AI signal ranking</div>
                <div className="text-xs text-muted">Surface stronger ideas first</div>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-[1.2rem] border border-white/5 bg-black/10 px-4 py-3">
              <ArrowDownRight className="h-5 w-5 text-negative" />
              <div>
                <div className="text-sm font-semibold text-white">Risk-aware negatives</div>
                <div className="text-xs text-muted">Spot weak setups early</div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-10 rounded-[2rem] border border-white/10 bg-black/15 p-6 shadow-[0_12px_35px_rgba(2,6,23,0.24)] backdrop-blur sm:p-8">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-[1.2fr_1.2fr_1.2fr_0.55fr_0.55fr]">
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search symbol or company"
              className="control-field"
            />
            <select
              value={sector}
              onChange={(event) => setSector(event.target.value)}
              className="control-field"
            >
              {sectors.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
            <select
              value={signal}
              onChange={(event) => setSignal(event.target.value)}
              className="control-field"
            >
              {['ALL', 'BUY', 'SELL', 'HOLD'].map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
            <input
              value={minRsi}
              onChange={(event) => setMinRsi(event.target.value)}
              type="number"
              placeholder="Min RSI"
              className="control-field"
            />
            <input
              value={maxRsi}
              onChange={(event) => setMaxRsi(event.target.value)}
              type="number"
              placeholder="Max RSI"
              className="control-field"
            />
          </div>

          <div className="mt-4 grid gap-4 sm:max-w-[22rem] sm:grid-cols-2">
            <input
              value={minSentiment}
              onChange={(event) => setMinSentiment(event.target.value)}
              type="number"
              step="0.1"
              placeholder="Min Sentiment"
              className="control-field"
            />
            <input
              value={maxSentiment}
              onChange={(event) => setMaxSentiment(event.target.value)}
              type="number"
              step="0.1"
              placeholder="Max Sentiment"
              className="control-field"
            />
          </div>
        </div>
      </section>

      {isLoading ? (
        <TableSkeleton />
      ) : showError ? (
        <div className="rounded-[2rem] border border-negative/25 bg-negative/10 px-6 py-8 text-center text-sm text-negative">
          Unable to load market and stock data from the backend. Refresh the page or restart the backend, then try again.
        </div>
      ) : (
        <div className="overflow-hidden rounded-[2rem] border border-white/10 bg-[#0f172a]/94 shadow-[0_26px_70px_rgba(2,6,23,0.38)]">
          <div className="flex flex-col gap-4 border-b border-white/10 bg-white/[0.03] px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="text-xs font-bold uppercase tracking-[0.24em] text-muted">Results Table</div>
              <div className="mt-2 font-display text-2xl font-bold text-white">
                {filtered.length} stocks match the current screen
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-[1.15rem] border border-positive/20 bg-positive/10 px-4 py-3">
                <div className="text-xs uppercase tracking-[0.18em] text-muted">Buy</div>
                <div className="mt-1 font-display text-xl font-bold text-positive">
                  {filtered.filter((stock) => stock.signal === 'BUY').length}
                </div>
              </div>
              <div className="rounded-[1.15rem] border border-amber-400/20 bg-amber-400/10 px-4 py-3">
                <div className="text-xs uppercase tracking-[0.18em] text-muted">Hold</div>
                <div className="mt-1 font-display text-xl font-bold text-amber-300">
                  {filtered.filter((stock) => stock.signal === 'HOLD').length}
                </div>
              </div>
              <div className="rounded-[1.15rem] border border-negative/20 bg-negative/10 px-4 py-3">
                <div className="text-xs uppercase tracking-[0.18em] text-muted">Sell</div>
                <div className="mt-1 font-display text-xl font-bold text-negative">
                  {filtered.filter((stock) => stock.signal === 'SELL').length}
                </div>
              </div>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="sticky top-0 z-10 bg-[#111827]/98 backdrop-blur">
                <tr className="border-b border-white/10">
                  {['Stock', 'Sector', 'Price', 'Change %', 'RSI', 'MACD', 'Sentiment', 'Signal', 'AI Prediction'].map((heading) => (
                    <th key={heading} className="whitespace-nowrap px-6 py-4 text-left text-[0.82rem] font-semibold uppercase tracking-[0.16em] text-muted">
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 bg-surface/95">
                {filtered.map((stock, index) => (
                  <tr key={stock.symbol} className={`${index % 2 === 0 ? 'bg-white/[0.01]' : 'bg-white/[0.035]'} transition duration-200 hover:bg-white/[0.07]`}>
                    <td className="px-6 py-6">
                      <Link
                        to={`/stocks/${stock.symbol}`}
                        onMouseEnter={() => prefetchStock(stock.symbol)}
                        onFocus={() => prefetchStock(stock.symbol)}
                        className="font-display text-[1.1rem] font-bold text-white transition hover:text-highlight"
                      >
                        {stock.symbol}
                      </Link>
                      <div className="mt-1 text-base text-muted">{stock.companyName}</div>
                    </td>
                    <td className="px-6 py-6 text-[1.05rem] text-muted">{stock.sector}</td>
                    <td className="px-6 py-6 text-[1.1rem] font-medium text-white">{formatCurrency(stock.price)}</td>
                    <td className={`px-6 py-6 text-[1.1rem] font-semibold ${stock.changePct >= 0 ? 'text-positive' : 'text-negative'}`}>
                      {formatPercent(stock.changePct)}
                    </td>
                    <td className="px-6 py-6 text-[1.05rem] text-ink">{formatNumber(stock.rsi, 1)}</td>
                    <td className="px-6 py-6 text-[1.05rem] text-ink">{formatNumber(stock.macd, 2)}</td>
                    <td className="px-6 py-6 text-[1.05rem] text-ink">{formatNumber(stock.sentimentScore, 2)}</td>
                    <td className="px-6 py-6">
                      <span className={`rounded-full px-4 py-2 text-sm font-semibold ${stock.signal === 'BUY' ? 'bg-positive/15 text-positive' : stock.signal === 'SELL' ? 'bg-negative/15 text-negative' : 'bg-neutral/15 text-amber-300'}`}>
                        {stock.signal}
                      </span>
                    </td>
                    <td className="px-6 py-6">
                      <div className="font-display text-[1.1rem] font-bold text-white">{stock.prediction}</div>
                      <div className="mt-1 text-sm text-muted">{Math.round(stock.confidence || 0)}% confidence</div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {!filtered.length ? (
            <div className="p-10 text-center text-base text-muted">No stocks match your current filters.</div>
          ) : null}
        </div>
      )}
    </div>
  );
}
