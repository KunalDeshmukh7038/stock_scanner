import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BrainCircuit,
  Building2,
  ChartCandlestick,
  CircleAlert,
  CircleCheckBig,
  Newspaper,
  Radar,
  Rows3,
  Sparkles,
} from 'lucide-react';
import {
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useParams } from 'react-router-dom';

import { DataTable } from '../components/DataTable';
import { Gauge } from '../components/Gauge';
import { CardSkeleton } from '../components/LoadingSkeleton';
import { SectionHeader } from '../components/SectionHeader';
import { SentimentBar } from '../components/SentimentBar';
import { TradingLayout } from '../components/TradingLayout';
import { api } from '../lib/api';
import { formatCompactNumber, formatCurrency, formatDate, formatNumber, formatPercent } from '../lib/formatters';

const tabs = ['Summary', 'Chart', 'Analysis', 'Sentiment', 'AI Prediction', 'Peers'];
const rangeDays = { '1M': 30, '6M': 180, '1Y': 365, '3Y': 1095, '5Y': 1825 };

function StatCard({ label, value, helper, icon: Icon, tone = 'default' }) {
  const tones = {
    default: 'border-white/10 bg-white/[0.03]',
    positive: 'border-positive/20 bg-positive/10',
    negative: 'border-negative/20 bg-negative/10',
    neutral: 'border-amber-400/20 bg-amber-400/10',
  };

  return (
    <div className={`rounded-[1.4rem] border p-5 shadow-[0_18px_38px_rgba(2,6,23,0.24)] transition duration-300 hover:-translate-y-1 hover:shadow-[0_22px_48px_rgba(2,6,23,0.32)] ${tones[tone]}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="text-xs uppercase tracking-[0.18em] text-muted">{label}</div>
        {Icon ? (
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-black/15 text-highlight shadow-sm">
            <Icon className="h-4 w-4" />
          </div>
        ) : null}
      </div>
      <div className="mt-3 font-display text-2xl font-bold tracking-tight text-white">{value}</div>
      {helper ? <div className="mt-2 text-sm text-muted">{helper}</div> : null}
    </div>
  );
}

function DetailBadge({ value, tone = 'default' }) {
  const tones = {
    default: 'border-white/10 bg-white/[0.03] text-muted',
    positive: 'border-positive/20 bg-positive/10 text-positive',
    negative: 'border-negative/20 bg-negative/10 text-negative',
    neutral: 'border-amber-400/20 bg-amber-400/10 text-amber-300',
  };

  return <div className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${tones[tone]}`}>{value}</div>;
}

function InsightList({ title, items, emptyText, tone = 'default', icon: Icon }) {
  const styles = {
    default: 'border border-white/10 bg-white/[0.03] text-muted',
    positive: 'border border-positive/15 bg-positive/10 text-positive',
    negative: 'border border-negative/15 bg-negative/10 text-negative',
  };

  return (
    <div className="panel p-6">
      <div className="flex items-center gap-3">
        {Icon ? (
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-black/15 text-highlight">
            <Icon className="h-4 w-4" />
          </div>
        ) : null}
        <h3 className="font-display text-xl font-bold text-white">{title}</h3>
      </div>
      <div className="mt-5 space-y-3 text-sm">
        {(items.length ? items : [emptyText]).map((item) => (
          <div key={item} className={`rounded-[1.2rem] px-4 py-3 leading-6 ${styles[tone]}`}>
            {item}
          </div>
        ))}
      </div>
    </div>
  );
}

function filterHistory(history, range) {
  const days = rangeDays[range];
  if (!days || !history.length) return history;

  const end = new Date(history.at(-1).date);
  return history.filter((point) => new Date(end) - new Date(point.date) <= days * 24 * 60 * 60 * 1000);
}

function buildSourceBreakdown(detail) {
  if (detail.sourceBreakdown.length) return detail.sourceBreakdown;

  const counts = detail.news.reduce((accumulator, item) => {
    const source = item.source || 'Unknown';
    accumulator[source] = (accumulator[source] || 0) + 1;
    return accumulator;
  }, {});

  return Object.entries(counts).map(([source, count]) => ({ id: source, source, count }));
}

function signalTone(signal) {
  if (signal === 'BUY') return 'positive';
  if (signal === 'SELL') return 'negative';
  return 'neutral';
}

function changeTone(value) {
  return Number(value || 0) >= 0 ? 'positive' : 'negative';
}

function analysisSummary(point, detail) {
  const rsiValue = Number(point.rsi || detail.rsi || 0);
  const macdValue = Number(point.macd || detail.macd || 0);
  const volumeValue = Number(point.volumeChange || 0);

  if (rsiValue >= 65 && macdValue > 0) return 'Momentum is constructive with RSI in stronger territory and MACD still supportive.';
  if (rsiValue <= 35 && macdValue < 0) return 'Technical pressure remains visible with weaker momentum and a softer MACD posture.';
  if (volumeValue > 10) return 'Participation is improving, with volume expanding faster than the recent baseline.';
  return 'Indicators are mixed, so use chart structure and sentiment context before acting on the signal.';
}

function formatFundamentalValue(value, suffix = '') {
  if (value === null || value === undefined || value === '') return 'N/A';
  return `${formatNumber(value, 2)}${suffix}`;
}

function createPlaceholderDetail(stock, symbol) {
  if (!stock) return undefined;

  return {
    ...stock,
    symbol: stock.symbol || symbol,
    companyName: stock.companyName || symbol,
    about: stock.about || `${stock.companyName || symbol} is being loaded with the full research view.`,
    keyPoints: stock.keyPoints || [],
    pros: stock.pros || [],
    cons: stock.cons || [],
    history: [],
    news: [],
    featureImportance: [],
    peers: [],
    sourceBreakdown: [],
    modelUsed: stock.modelUsed || 'Loading detailed model context',
    marketCap: stock.marketCap || 0,
    pe: stock.pe || 0,
    bookValue: stock.bookValue || 0,
    roe: stock.roe || 0,
    roce: stock.roce || 0,
    dividendYield: stock.dividendYield || 0,
    faceValue: stock.faceValue || 0,
    weekHigh52: stock.weekHigh52 || stock.high || 0,
    weekLow52: stock.weekLow52 || stock.low || 0,
  };
}

export function StockDetailPage() {
  const { symbol = '' } = useParams();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('Summary');
  const [chartRange, setChartRange] = useState('1Y');

  const stockQuery = useQuery({
    queryKey: ['stock-detail', symbol],
    queryFn: () => api.getStock(symbol),
    placeholderData: () => {
      const bootstrap = queryClient.getQueryData(['bootstrap']);
      const cachedStock = bootstrap?.stocks?.find((item) => item.symbol === symbol);
      return createPlaceholderDetail(cachedStock, symbol);
    },
  });

  if (stockQuery.isLoading) return <CardSkeleton count={4} />;
  if (stockQuery.isError || !stockQuery.data) {
    return <div className="panel p-8 text-center text-sm text-muted">Unable to load stock details from the API.</div>;
  }

  const detail = stockQuery.data;
  const bootstrapStocks = queryClient.getQueryData(['bootstrap'])?.stocks || [];
  const history = filterHistory(detail.history || [], chartRange);
  const latestPoint = history.at(-1) || detail.history?.at(-1) || {};
  const sourceBreakdown = buildSourceBreakdown(detail);
  const priceDirection = changeTone(detail.changePct);
  const priceDirectionClass = priceDirection === 'positive' ? 'text-emerald-700' : 'text-rose-700';
  const signalClass = signalTone(detail.signal);
  const latestClose = detail.price || latestPoint.close || 0;
  const watchlistItems = (
    detail.peers?.length
      ? detail.peers
      : bootstrapStocks.filter((item) => item.symbol !== detail.symbol).slice(0, 8)
  ).slice(0, 8);

  return (
    <div className="space-y-8">
      <section className="overflow-hidden rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.24),_transparent_24%),radial-gradient(circle_at_top_right,_rgba(34,197,94,0.16),_transparent_22%),linear-gradient(180deg,rgba(15,23,42,0.96),rgba(11,15,25,0.98))] shadow-[0_30px_80px_rgba(2,6,23,0.45)]">
        <div className="grid gap-8 px-6 py-8 sm:px-8 lg:grid-cols-[1.2fr_0.8fr] lg:px-10 lg:py-10">
          <div className="space-y-6">
            <div className="flex flex-wrap items-center gap-3">
              <DetailBadge value={detail.sector} />
              <DetailBadge value={detail.symbol} />
              <DetailBadge value={detail.signal} tone={signalClass} />
              <DetailBadge value={`${detail.prediction} | ${Math.round(detail.confidence || 0)}%`} tone={signalClass} />
            </div>

            <div>
              <h1 className="font-display text-4xl font-bold tracking-tight text-white sm:text-5xl">
                {detail.companyName}
              </h1>
              <p className="mt-4 max-w-3xl text-base leading-8 text-muted">{detail.about}</p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <StatCard label="Current Price" value={formatCurrency(latestClose)} helper="Live or latest backend quote" icon={ChartCandlestick} />
              <StatCard
                label="Day Change"
                value={formatPercent(detail.changePct)}
                helper={priceDirection === 'positive' ? 'Price is trading above previous close.' : 'Price is trading below previous close.'}
                icon={priceDirection === 'positive' ? ArrowUpRight : ArrowDownRight}
                tone={priceDirection}
              />
              <StatCard label="Overall Sentiment" value={formatNumber(detail.sentimentScore, 2)} helper="News and narrative tone" icon={Newspaper} />
              <StatCard label="Model Used" value={detail.modelUsed} helper="Current prediction engine" icon={BrainCircuit} />
            </div>
          </div>

          <div className="grid gap-4 self-start">
            <div className="glass-card p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.2em] text-muted">Research Snapshot</div>
                  <div className="mt-2 font-display text-3xl font-bold text-white">{formatCurrency(latestClose)}</div>
                </div>
                <div className={`rounded-full px-4 py-2 text-sm font-semibold ${priceDirectionClass} ${priceDirection === 'positive' ? 'bg-positive/15' : 'bg-negative/15'}`}>
                  {formatPercent(detail.changePct)}
                </div>
              </div>

              <div className="mt-6 grid grid-cols-2 gap-4">
                <div className="rounded-[1.25rem] border border-white/10 bg-black/10 px-4 py-4">
                  <div className="text-xs uppercase tracking-[0.18em] text-muted">Market Cap</div>
                  <div className="mt-2 font-display text-xl font-bold text-white">{formatCompactNumber(detail.marketCap)}</div>
                </div>
                <div className="rounded-[1.25rem] border border-white/10 bg-black/10 px-4 py-4">
                  <div className="text-xs uppercase tracking-[0.18em] text-muted">P/E</div>
                  <div className="mt-2 font-display text-xl font-bold text-white">{formatNumber(detail.pe, 2)}</div>
                </div>
                <div className="rounded-[1.25rem] border border-white/10 bg-black/10 px-4 py-4">
                  <div className="text-xs uppercase tracking-[0.18em] text-muted">52W High</div>
                  <div className="mt-2 font-display text-xl font-bold text-white">{formatCurrency(detail.weekHigh52 || detail.high)}</div>
                </div>
                <div className="rounded-[1.25rem] border border-white/10 bg-black/10 px-4 py-4">
                  <div className="text-xs uppercase tracking-[0.18em] text-muted">52W Low</div>
                  <div className="mt-2 font-display text-xl font-bold text-white">{formatCurrency(detail.weekLow52 || detail.low)}</div>
                </div>
              </div>
            </div>

            <div className="glass-card p-6">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-black/15 text-highlight">
                  <Radar className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.2em] text-muted">AI Thesis</div>
                  <div className="font-display text-xl font-bold text-white">{detail.signal} setup with {detail.prediction} bias</div>
                </div>
              </div>
              <p className="mt-4 text-sm leading-7 text-muted">
                Confidence is currently {Math.round(detail.confidence || 0)}%, with the model balancing technical indicators and the latest sentiment profile.
              </p>
            </div>
          </div>
        </div>
      </section>

      <div className="sticky top-[84px] z-40 overflow-x-auto rounded-[1.6rem] border border-white/10 bg-[#0f172a]/88 p-2 shadow-panel backdrop-blur-2xl">
        <div className="flex w-max min-w-full gap-2">
          {tabs.map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
              className={`rounded-[1.1rem] px-4 py-3 text-sm font-semibold transition duration-300 ${activeTab === tab ? 'bg-highlight text-white shadow-[0_12px_28px_rgba(59,130,246,0.28)]' : 'text-muted hover:bg-white/[0.05] hover:text-white'}`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {activeTab === 'Summary' ? (
        <section className="fade-in space-y-8">
          <SectionHeader
            eyebrow="Summary"
            title="Business quality, valuation, and quick investment context"
            subtitle="A cleaner screener-style snapshot of the company, its metrics, and the strongest positives or risks right now."
          />
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="ROE" value={formatFundamentalValue(detail.roe, '%')} icon={Sparkles} />
            <StatCard label="ROCE" value={formatFundamentalValue(detail.roce, '%')} icon={Activity} />
            <StatCard label="Dividend Yield" value={formatFundamentalValue(detail.dividendYield, '%')} icon={CircleCheckBig} />
            <StatCard label="Face Value" value={formatFundamentalValue(detail.faceValue)} icon={Building2} />
          </div>
          <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
            <div className="grid gap-6">
              <div className="panel p-6">
                <h3 className="font-display text-xl font-bold text-white">About company</h3>
                <p className="mt-4 text-sm leading-8 text-muted">{detail.about}</p>
              </div>
              <div className="panel p-6">
                <h3 className="font-display text-xl font-bold text-white">Quick facts</h3>
                <div className="mt-5 grid gap-4 sm:grid-cols-2">
                  <div className="rounded-[1.2rem] border border-white/10 bg-white/[0.03] px-4 py-4">
                    <div className="text-xs uppercase tracking-[0.18em] text-muted">High / Low</div>
                    <div className="mt-2 font-display text-lg font-bold text-white">
                      {formatCurrency(detail.high)} / {formatCurrency(detail.low)}
                    </div>
                  </div>
                  <div className="rounded-[1.2rem] border border-white/10 bg-white/[0.03] px-4 py-4">
                    <div className="text-xs uppercase tracking-[0.18em] text-muted">Book Value</div>
                    <div className="mt-2 font-display text-lg font-bold text-white">{formatNumber(detail.bookValue, 2)}</div>
                  </div>
                  <div className="rounded-[1.2rem] border border-white/10 bg-white/[0.03] px-4 py-4">
                    <div className="text-xs uppercase tracking-[0.18em] text-muted">Prediction</div>
                    <div className="mt-2 font-display text-lg font-bold text-white">{detail.prediction}</div>
                  </div>
                  <div className="rounded-[1.2rem] border border-white/10 bg-white/[0.03] px-4 py-4">
                    <div className="text-xs uppercase tracking-[0.18em] text-muted">Confidence</div>
                    <div className="mt-2 font-display text-lg font-bold text-white">{Math.round(detail.confidence || 0)}%</div>
                  </div>
                </div>
              </div>
            </div>
            <div className="grid gap-6">
              <InsightList
                title="Key points"
                items={detail.keyPoints}
                emptyText="API did not provide key points yet."
                icon={Rows3}
              />
              <InsightList
                title="Pros"
                items={detail.pros}
                emptyText="No positive highlights were returned."
                tone="positive"
                icon={CircleCheckBig}
              />
              <InsightList
                title="Cons"
                items={detail.cons}
                emptyText="No risk flags were returned."
                tone="negative"
                icon={CircleAlert}
              />
            </div>
          </div>
        </section>
      ) : null}

      {activeTab === 'Chart' ? (
        <section className="fade-in space-y-6">
          <TradingLayout
            detail={detail}
            history={history}
            currentPrice={latestPoint.close || latestClose}
            watchlistItems={watchlistItems}
            activeRange={chartRange}
            onRangeChange={setChartRange}
            rangeOptions={Object.keys(rangeDays)}
          />
        </section>
      ) : null}

      {activeTab === 'Analysis' ? (
        <section className="fade-in space-y-6">
          <SectionHeader
            eyebrow="Analysis"
            title="Technical indicator workspace"
            subtitle="Use the gauges and comparison charts to understand the quality of the current setup."
          />
          <div className="grid gap-6 xl:grid-cols-[0.72fr_1.28fr]">
            <div className="grid gap-6">
              <Gauge value={latestPoint.rsi || detail.rsi} label="RSI Gauge" color="#22C55E" />
              <div className="panel p-6">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Technical pulse</div>
                <p className="mt-4 text-sm leading-7 text-muted">{analysisSummary(latestPoint, detail)}</p>
              </div>
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
                <StatCard label="ATR" value={formatNumber(latestPoint.atr, 2)} icon={Activity} />
                <StatCard label="Momentum" value={formatNumber(latestPoint.momentum, 2)} icon={ArrowUpRight} tone={Number(latestPoint.momentum || 0) >= 0 ? 'positive' : 'negative'} />
                <StatCard label="Volume Change" value={`${formatNumber(latestPoint.volumeChange, 2)}%`} icon={Building2} tone={Number(latestPoint.volumeChange || 0) >= 0 ? 'positive' : 'negative'} />
              </div>
            </div>
            <div className="grid gap-6">
              <div className="panel p-4 sm:p-6">
                <div className="mb-4 font-display text-lg font-bold text-white">MACD vs Signal</div>
                <div className="h-[280px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={history}>
                      <CartesianGrid stroke="#243041" strokeDasharray="3 3" />
                      <XAxis dataKey="date" tickFormatter={formatDate} minTickGap={40} tick={{ fill: '#9CA3AF', fontSize: 12 }} />
                      <YAxis tick={{ fill: '#9CA3AF', fontSize: 12 }} />
                      <Tooltip labelFormatter={(value) => formatDate(value)} contentStyle={{ borderRadius: 16, borderColor: '#243041', backgroundColor: '#0f172a', color: '#E5E7EB' }} />
                      <Bar dataKey="macd" fill="#22C55E" radius={[6, 6, 0, 0]} />
                      <Line type="monotone" dataKey="signal" stroke="#EF4444" strokeWidth={3} dot={false} />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <div className="panel p-4 sm:p-6">
                <div className="mb-4 font-display text-lg font-bold text-white">Bollinger Bands</div>
                <div className="h-[280px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={history}>
                      <CartesianGrid stroke="#243041" strokeDasharray="3 3" />
                      <XAxis dataKey="date" tickFormatter={formatDate} minTickGap={40} tick={{ fill: '#9CA3AF', fontSize: 12 }} />
                      <YAxis tick={{ fill: '#9CA3AF', fontSize: 12 }} />
                      <Tooltip labelFormatter={(value) => formatDate(value)} contentStyle={{ borderRadius: 16, borderColor: '#243041', backgroundColor: '#0f172a', color: '#E5E7EB' }} />
                      <Line type="monotone" dataKey="bbUpper" stroke="#94A3B8" dot={false} />
                      <Line type="monotone" dataKey="close" stroke="#22C55E" strokeWidth={3} dot={false} />
                      <Line type="monotone" dataKey="bbLower" stroke="#94A3B8" dot={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        </section>
      ) : null}

      {activeTab === 'Sentiment' ? (
        <section className="fade-in space-y-6">
          <SectionHeader
            eyebrow="Sentiment"
            title="News intelligence and source mix"
            subtitle="Track the balance of positive, neutral, and negative coverage with the latest linked stories."
          />
          <div className="grid gap-6 xl:grid-cols-[0.75fr_1.25fr]">
            <div className="space-y-6">
              <div className="panel p-6">
                <div className="text-xs uppercase tracking-[0.18em] text-muted">Overall sentiment score</div>
                <div className="mt-4">
                  <SentimentBar value={detail.sentimentScore} />
                </div>
              </div>
              <div className="panel p-4 sm:p-6">
                <div className="mb-4 font-display text-lg font-bold text-white">Source breakdown</div>
                <div className="h-[260px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={sourceBreakdown}>
                      <CartesianGrid stroke="#243041" strokeDasharray="3 3" />
                      <XAxis dataKey="source" hide />
                      <YAxis tick={{ fill: '#9CA3AF', fontSize: 12 }} />
                      <Tooltip contentStyle={{ borderRadius: 16, borderColor: '#243041', backgroundColor: '#0f172a', color: '#E5E7EB' }} />
                      <Bar dataKey="count" fill="#3B82F6" radius={[8, 8, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
            <div className="panel p-6">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-black/15 text-highlight">
                  <Newspaper className="h-5 w-5" />
                </div>
                <div className="font-display text-xl font-bold text-white">Latest news</div>
              </div>
              <div className="mt-5 space-y-4">
                {detail.news.length ? detail.news.map((item) => (
                  <a key={item.id} href={item.url} target="_blank" rel="noreferrer" className="block rounded-[1.4rem] border border-white/10 bg-white/[0.03] p-4 transition duration-300 hover:border-positive/35 hover:bg-white/[0.06]">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="font-semibold leading-7 text-white">{item.title}</div>
                        <div className="mt-2 text-xs text-muted">{item.source} | {formatDate(item.publishedAt)}</div>
                      </div>
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${item.sentiment > 0.1 ? 'bg-positive/10 text-positive' : item.sentiment < -0.1 ? 'bg-negative/10 text-negative' : 'bg-neutral/10 text-neutral'}`}>
                        {item.sentiment > 0.1 ? 'Positive' : item.sentiment < -0.1 ? 'Negative' : 'Neutral'}
                      </span>
                    </div>
                  </a>
                )) : <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.03] p-6 text-sm text-muted">No news stories were returned by the API.</div>}
              </div>
            </div>
          </div>
        </section>
      ) : null}

      {activeTab === 'AI Prediction' ? (
        <section className="fade-in space-y-6">
          <SectionHeader
            eyebrow="AI Prediction"
            title="Model output and feature importance"
            subtitle="Review the direction, conviction level, and the features most responsible for the current model view."
          />
          <div className="grid gap-6 xl:grid-cols-[0.72fr_1.28fr]">
            <div className="grid gap-4">
              <StatCard label="Prediction" value={detail.prediction} icon={BrainCircuit} tone={signalClass} />
              <StatCard label="Confidence" value={`${Math.round(detail.confidence || 0)}%`} icon={Sparkles} />
              <StatCard label="Model Used" value={detail.modelUsed} icon={Activity} />
              <div className="panel p-6">
                <div className="text-xs uppercase tracking-[0.18em] text-muted">AI read</div>
                <p className="mt-4 text-sm leading-7 text-muted">
                  The current model leans {detail.prediction.toLowerCase()} with a {detail.signal.toLowerCase()} signal, using the latest technical and sentiment context available from the backend.
                </p>
              </div>
            </div>
            <div className="panel p-4 sm:p-6">
              <div className="mb-4 font-display text-lg font-bold text-white">Feature importance</div>
              {detail.featureImportance.length ? (
                <div className="h-[360px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={detail.featureImportance} layout="vertical" margin={{ left: 16 }}>
                      <CartesianGrid stroke="#243041" strokeDasharray="3 3" />
                      <XAxis type="number" tick={{ fill: '#9CA3AF', fontSize: 12 }} />
                      <YAxis type="category" dataKey="feature" width={120} tick={{ fill: '#9CA3AF', fontSize: 12 }} />
                      <Tooltip contentStyle={{ borderRadius: 16, borderColor: '#243041', backgroundColor: '#0f172a', color: '#E5E7EB' }} />
                      <Bar dataKey="value" fill="#22C55E" radius={[0, 8, 8, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.03] p-6 text-sm text-muted">Feature importance is not available from the API yet.</div>
              )}
            </div>
          </div>
        </section>
      ) : null}

      {activeTab === 'Peers' ? (
        <section className="fade-in space-y-6">
          <SectionHeader
            eyebrow="Peers"
            title="Sector comparison"
            subtitle="Benchmark this name against a smaller peer set on valuation, size, and model signal."
          />
          <DataTable
            rows={detail.peers}
            emptyMessage="Peer comparison is not available."
            columns={[
              { key: 'symbol', label: 'Symbol' },
              { key: 'companyName', label: 'Company' },
              { key: 'sector', label: 'Sector' },
              { key: 'price', label: 'Price', currency: true },
              { key: 'pe', label: 'P/E', numeric: true },
              { key: 'roe', label: 'ROE', numeric: true },
              { key: 'marketCap', label: 'Market Cap', numeric: true },
              { key: 'signal', label: 'AI Signal' },
            ]}
          />
        </section>
      ) : null}
    </div>
  );
}
