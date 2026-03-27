import { useMemo, useState } from 'react';
import { Activity, ChevronsUpDown, LineChart, SlidersHorizontal } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { CandlestickChart } from './CandlestickChart';
import { formatDate, formatNumber } from '../lib/formatters';

const tradingFrames = ['1m', '5m', '1D', '1W'];

function ToolbarButton({ active = false, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full border px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] transition duration-200 ${
        active
          ? 'border-[#3B82F6]/40 bg-[#3B82F6]/16 text-white'
          : 'border-white/10 bg-white/[0.03] text-[#9CA3AF] hover:border-white/20 hover:bg-white/[0.06] hover:text-white'
      }`}
    >
      {children}
    </button>
  );
}

export function ChartArea({ history = [], activeRange, onRangeChange, rangeOptions = [] }) {
  const [activeFrame, setActiveFrame] = useState('1D');

  const rsiData = useMemo(
    () => history.map((point) => ({ date: point.date, rsi: Number(point.rsi || 0), volume: Number(point.volume || 0) })),
    [history],
  );

  return (
    <div className="grid h-full gap-4 xl:grid-rows-[minmax(0,0.72fr)_minmax(260px,0.28fr)]">
      <div className="rounded-[1.5rem] border border-white/10 bg-[#111827]/94 shadow-[0_28px_60px_rgba(2,6,23,0.4)] backdrop-blur-xl">
        <div className="sticky top-0 z-10 flex flex-col gap-4 rounded-t-[1.5rem] border-b border-white/10 bg-[#111827]/95 px-4 py-4 backdrop-blur-xl sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-col gap-3">
            <div className="flex flex-wrap items-center gap-2">
              {tradingFrames.map((frame) => (
                <ToolbarButton key={frame} active={activeFrame === frame} onClick={() => setActiveFrame(frame)}>
                  {frame}
                </ToolbarButton>
              ))}
            </div>
            {rangeOptions.length ? (
              <div className="flex flex-wrap items-center gap-2">
                {rangeOptions.map((range) => (
                  <button
                    key={range}
                    type="button"
                    onClick={() => onRangeChange?.(range)}
                    className={`rounded-full border px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] transition duration-200 ${
                      activeRange === range
                        ? 'border-[#22C55E]/35 bg-[#22C55E]/14 text-white'
                        : 'border-white/10 bg-white/[0.03] text-[#9CA3AF] hover:border-white/20 hover:bg-white/[0.06] hover:text-white'
                    }`}
                  >
                    {range}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#9CA3AF] transition duration-200 hover:border-white/20 hover:bg-white/[0.06] hover:text-white"
            >
              <Activity className="h-3.5 w-3.5" />
              Indicators
            </button>
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#9CA3AF] transition duration-200 hover:border-white/20 hover:bg-white/[0.06] hover:text-white"
            >
              <LineChart className="h-3.5 w-3.5" />
              Layout
            </button>
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#9CA3AF] transition duration-200 hover:border-white/20 hover:bg-white/[0.06] hover:text-white"
            >
              <SlidersHorizontal className="h-3.5 w-3.5" />
              Tools
            </button>
          </div>
        </div>

        <div className="p-4">
          <div className="rounded-[1.25rem] border border-[#3B82F6]/15 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.12),_transparent_34%),linear-gradient(180deg,rgba(11,17,32,0.94),rgba(15,23,42,0.98))] shadow-[0_0_0_1px_rgba(59,130,246,0.08),0_20px_40px_rgba(2,6,23,0.28)]">
            <CandlestickChart data={history} initialMode="candle" />
          </div>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-[1.35rem] border border-white/10 bg-[#111827]/92 p-4 shadow-[0_20px_36px_rgba(2,6,23,0.28)] backdrop-blur-xl">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#9CA3AF]">Volume</div>
              <div className="mt-1 font-display text-lg font-semibold text-white">Session participation</div>
            </div>
            <div className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-[11px] text-[#9CA3AF]">
              Auto
            </div>
          </div>
          <div className="h-[190px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={rsiData}>
                <defs>
                  <linearGradient id="volumeFillTerminal" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#3B82F6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#243041" strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={formatDate} minTickGap={48} tick={{ fill: '#9CA3AF', fontSize: 11 }} />
                <YAxis tick={{ fill: '#9CA3AF', fontSize: 11 }} tickFormatter={(value) => formatNumber(value, 0)} />
                <Tooltip
                  labelFormatter={(value) => formatDate(value)}
                  formatter={(value) => [formatNumber(value, 0), 'Volume']}
                  contentStyle={{ borderRadius: 16, borderColor: '#243041', backgroundColor: '#0f172a', color: '#E5E7EB' }}
                />
                <Area type="monotone" dataKey="volume" stroke="#3B82F6" fill="url(#volumeFillTerminal)" strokeWidth={2.5} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-[1.35rem] border border-white/10 bg-[#111827]/92 p-4 shadow-[0_20px_36px_rgba(2,6,23,0.28)] backdrop-blur-xl">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#9CA3AF]">RSI Panel</div>
              <div className="mt-1 font-display text-lg font-semibold text-white">Momentum monitor</div>
            </div>
            <div className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-[11px] text-[#9CA3AF]">
              <ChevronsUpDown className="h-3.5 w-3.5" />
              14
            </div>
          </div>
          <div className="h-[190px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={rsiData}>
                <defs>
                  <linearGradient id="rsiFillTerminal" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#22C55E" stopOpacity={0.25} />
                    <stop offset="100%" stopColor="#22C55E" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#243041" strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={formatDate} minTickGap={48} tick={{ fill: '#9CA3AF', fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fill: '#9CA3AF', fontSize: 11 }} />
                <Tooltip
                  labelFormatter={(value) => formatDate(value)}
                  formatter={(value) => [formatNumber(value, 2), 'RSI']}
                  contentStyle={{ borderRadius: 16, borderColor: '#243041', backgroundColor: '#0f172a', color: '#E5E7EB' }}
                />
                <Area type="monotone" dataKey="rsi" stroke="#22C55E" fill="url(#rsiFillTerminal)" strokeWidth={2.5} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
