import { useEffect, useMemo, useState } from 'react';
import { ChartCandlestick, LineChart, RotateCcw, ZoomIn, ZoomOut } from 'lucide-react';

import { formatCurrency, formatDate, formatNumber } from '../lib/formatters';

const CHART_WIDTH = 1100;
const CHART_HEIGHT = 500;
const MARGIN = { top: 26, right: 70, bottom: 74, left: 84 };
const VOLUME_HEIGHT = 78;
const MIN_VISIBLE_POINTS = 24;

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function clampCandleWidth(width) {
  return Math.max(4, Math.min(14, width));
}

function priceValue(point, key) {
  return Number(point?.[key] ?? 0);
}

function toPoint(dataPoint, index) {
  const open = priceValue(dataPoint, 'open') || priceValue(dataPoint, 'close');
  const close = priceValue(dataPoint, 'close') || open;
  const high = priceValue(dataPoint, 'high') || Math.max(open, close);
  const low = priceValue(dataPoint, 'low') || Math.min(open, close);
  const volume = Number(dataPoint?.volume ?? 0);

  return {
    raw: dataPoint,
    index,
    date: dataPoint?.date,
    open,
    high,
    low,
    close,
    volume,
    sma50: Number(dataPoint?.sma50 ?? 0),
    sma200: Number(dataPoint?.sma200 ?? 0),
  };
}

function ControlButton({ active = false, onClick, title, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold transition duration-200 ${
        active
          ? 'border-[#3B82F6]/50 bg-[#3B82F6]/16 text-white shadow-[0_10px_25px_rgba(59,130,246,0.22)]'
          : 'border-white/10 bg-white/[0.03] text-[#9CA3AF] hover:border-white/20 hover:bg-white/[0.06] hover:text-white'
      }`}
    >
      {children}
    </button>
  );
}

function ChartTooltip({ point, x, y }) {
  if (!point) return null;

  const tooltipX = clamp(x + 18, 16, CHART_WIDTH - 220);
  const tooltipY = clamp(y - 18, 18, CHART_HEIGHT - 176);

  return (
    <foreignObject x={tooltipX} y={tooltipY} width="208" height="150">
      <div className="rounded-2xl border border-white/10 bg-[#0b1120]/96 p-4 text-xs text-[#E5E7EB] shadow-[0_18px_40px_rgba(2,6,23,0.45)] backdrop-blur-xl">
        <div className="font-semibold text-white">{formatDate(point.date)}</div>
        <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-[#9CA3AF]">
          <span>O: <span className="font-medium text-[#E5E7EB]">{formatNumber(point.open, 2)}</span></span>
          <span>H: <span className="font-medium text-[#E5E7EB]">{formatNumber(point.high, 2)}</span></span>
          <span>L: <span className="font-medium text-[#E5E7EB]">{formatNumber(point.low, 2)}</span></span>
          <span>C: <span className="font-medium text-[#E5E7EB]">{formatNumber(point.close, 2)}</span></span>
        </div>
        <div className="mt-3 border-t border-white/10 pt-2 text-[#9CA3AF]">
          Volume: <span className="font-medium text-[#E5E7EB]">{formatNumber(point.volume, 0)}</span>
        </div>
      </div>
    </foreignObject>
  );
}

export function CandlestickChart({ data = [], initialMode = 'line' }) {
  const parsedData = useMemo(() => data.map((point, index) => toPoint(point, index)), [data]);
  const totalPoints = parsedData.length;
  const defaultVisiblePoints = Math.max(MIN_VISIBLE_POINTS, Math.min(totalPoints, 180));

  const [mode, setMode] = useState(initialMode);
  const [viewport, setViewport] = useState({ start: 0, count: defaultVisiblePoints });
  const [hoverState, setHoverState] = useState(null);
  const [dragState, setDragState] = useState(null);

  useEffect(() => {
    setMode(initialMode);
  }, [initialMode]);

  useEffect(() => {
    if (!totalPoints) {
      setViewport({ start: 0, count: MIN_VISIBLE_POINTS });
      return;
    }

    const nextCount = clamp(viewport.count || defaultVisiblePoints, MIN_VISIBLE_POINTS, totalPoints);
    const nextStart = clamp(totalPoints - nextCount, 0, Math.max(totalPoints - nextCount, 0));
    setViewport({ start: nextStart, count: nextCount });
  }, [totalPoints]);

  const plotWidth = CHART_WIDTH - MARGIN.left - MARGIN.right;
  const pricePlotHeight = CHART_HEIGHT - MARGIN.top - MARGIN.bottom - VOLUME_HEIGHT;
  const volumeTop = MARGIN.top + pricePlotHeight + 22;
  const volumeBottom = CHART_HEIGHT - MARGIN.bottom;

  const visibleCount = clamp(viewport.count, MIN_VISIBLE_POINTS, Math.max(totalPoints, MIN_VISIBLE_POINTS));
  const maxStart = Math.max(totalPoints - visibleCount, 0);
  const visibleStart = clamp(viewport.start, 0, maxStart);
  const visibleData = parsedData.slice(visibleStart, visibleStart + visibleCount);

  const xStep = plotWidth / Math.max(visibleData.length, 1);
  const candleWidth = clampCandleWidth(xStep * 0.62);

  const priceSeriesValues = visibleData.flatMap((point) => [
    point.high,
    point.low,
    point.close,
    point.sma50 || point.close,
    point.sma200 || point.close,
  ]);
  const minPrice = Math.min(...priceSeriesValues);
  const maxPrice = Math.max(...priceSeriesValues);
  const padding = (maxPrice - minPrice || 1) * 0.08;
  const yMin = minPrice - padding;
  const yMax = maxPrice + padding;
  const maxVolume = Math.max(...visibleData.map((point) => point.volume || 0), 1);

  const yScale = (value) => MARGIN.top + ((yMax - value) / (yMax - yMin || 1)) * pricePlotHeight;
  const volumeScale = (value) => volumeBottom - ((value || 0) / maxVolume) * (VOLUME_HEIGHT - 12);

  const visiblePoints = visibleData.map((point, index) => {
    const x = MARGIN.left + index * xStep + xStep / 2;
    return { ...point, x };
  });

  const horizontalTicks = Array.from({ length: 5 }, (_, index) => {
    const ratio = index / 4;
    const value = yMax - ratio * (yMax - yMin);
    return {
      value,
      y: MARGIN.top + ratio * pricePlotHeight,
    };
  });

  const verticalTicks = Array.from({ length: Math.min(6, visiblePoints.length || 1) }, (_, index) => {
    const dataIndex = Math.min(visiblePoints.length - 1, Math.floor((index / Math.max(Math.min(6, visiblePoints.length || 1) - 1, 1)) * (visiblePoints.length - 1)));
    return {
      label: formatDate(visiblePoints[dataIndex]?.date),
      x: visiblePoints[dataIndex]?.x ?? MARGIN.left,
    };
  });

  const closePath = visiblePoints
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${yScale(point.close)}`)
    .join(' ');
  const fillPath = closePath
    ? `${closePath} L ${visiblePoints.at(-1)?.x ?? MARGIN.left} ${MARGIN.top + pricePlotHeight} L ${visiblePoints[0]?.x ?? MARGIN.left} ${MARGIN.top + pricePlotHeight} Z`
    : '';
  const sma50Path = visiblePoints
    .filter((point) => point.sma50)
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${yScale(point.sma50)}`)
    .join(' ');
  const sma200Path = visiblePoints
    .filter((point) => point.sma200)
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${yScale(point.sma200)}`)
    .join(' ');

  const activePoint = hoverState?.point ?? null;

  const updateHover = (clientX, clientY, bounds) => {
    if (!visiblePoints.length) return;
    const relativeX = clamp(clientX - bounds.left, MARGIN.left, CHART_WIDTH - MARGIN.right);
    const relativeY = clamp(clientY - bounds.top, MARGIN.top, volumeBottom);
    const nearestIndex = clamp(Math.round((relativeX - MARGIN.left - xStep / 2) / Math.max(xStep, 1)), 0, visiblePoints.length - 1);
    const point = visiblePoints[nearestIndex];

    setHoverState({
      point,
      x: point.x,
      y: clamp(relativeY, MARGIN.top, MARGIN.top + pricePlotHeight),
    });
  };

  const applyZoom = (nextCount, focusRatio = 0.5) => {
    if (!totalPoints) return;

    const clampedCount = clamp(Math.round(nextCount), MIN_VISIBLE_POINTS, totalPoints);
    const centerIndex = visibleStart + focusRatio * Math.max(visibleCount - 1, 0);
    const nextStart = clamp(Math.round(centerIndex - focusRatio * Math.max(clampedCount - 1, 0)), 0, Math.max(totalPoints - clampedCount, 0));
    setViewport({ start: nextStart, count: clampedCount });
  };

  const handleWheel = (event) => {
    if (!visiblePoints.length) return;
    event.preventDefault();
    const bounds = event.currentTarget.getBoundingClientRect();
    const relativeX = clamp(event.clientX - bounds.left, MARGIN.left, CHART_WIDTH - MARGIN.right);
    const focusRatio = clamp((relativeX - MARGIN.left) / Math.max(plotWidth, 1), 0, 1);
    const zoomFactor = event.deltaY < 0 ? 0.85 : 1.15;
    applyZoom(visibleCount * zoomFactor, focusRatio);
  };

  const handlePointerDown = (event) => {
    if (!visiblePoints.length) return;
    event.preventDefault();
    event.currentTarget.setPointerCapture?.(event.pointerId);
    setDragState({
      pointerId: event.pointerId,
      startClientX: event.clientX,
      startViewportStart: visibleStart,
    });
    updateHover(event.clientX, event.clientY, event.currentTarget.getBoundingClientRect());
  };

  const handlePointerMove = (event) => {
    const bounds = event.currentTarget.getBoundingClientRect();

    if (dragState && dragState.pointerId === event.pointerId) {
      const deltaX = event.clientX - dragState.startClientX;
      const deltaPoints = Math.round((deltaX / Math.max(plotWidth, 1)) * visibleCount);
      const nextStart = clamp(dragState.startViewportStart - deltaPoints, 0, maxStart);
      setViewport((current) => (current.start === nextStart ? current : { ...current, start: nextStart }));
    }

    updateHover(event.clientX, event.clientY, bounds);
  };

  const handlePointerUp = (event) => {
    event.currentTarget.releasePointerCapture?.(event.pointerId);
    setDragState(null);
  };

  if (!data.length) {
    return <div className="flex h-full items-center justify-center text-sm text-muted">No chart data available.</div>;
  }

  return (
    <div className="h-full w-full">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-muted">Price Structure</div>
          <div className="mt-2 font-display text-xl font-bold text-white">Line or candlestick view</div>
        </div>
        <div className="flex flex-wrap gap-2">
          <ControlButton active={mode === 'line'} onClick={() => setMode('line')} title="Line chart">
            <LineChart className="h-4 w-4" />
            Line
          </ControlButton>
          <ControlButton active={mode === 'candle'} onClick={() => setMode('candle')} title="Candlestick chart">
            <ChartCandlestick className="h-4 w-4" />
            Candle
          </ControlButton>
          <ControlButton onClick={() => applyZoom(visibleCount * 0.8)} title="Zoom in">
            <ZoomIn className="h-4 w-4" />
          </ControlButton>
          <ControlButton onClick={() => applyZoom(visibleCount * 1.2)} title="Zoom out">
            <ZoomOut className="h-4 w-4" />
          </ControlButton>
          <ControlButton onClick={() => setViewport({ start: 0, count: totalPoints || defaultVisiblePoints })} title="Reset zoom">
            <RotateCcw className="h-4 w-4" />
            Reset
          </ControlButton>
        </div>
      </div>

      <div className="relative h-[460px] overflow-hidden rounded-[1.35rem] border border-white/10 bg-[#0b1120]/90">
        <svg
          viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
          className="h-full w-full touch-none select-none"
          onWheel={handleWheel}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={() => {
            setHoverState(null);
            setDragState(null);
          }}
        >
          <defs>
            <linearGradient id="tradeLineFill" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#22C55E" stopOpacity={0.28} />
              <stop offset="100%" stopColor="#22C55E" stopOpacity={0} />
            </linearGradient>
          </defs>

          <rect x="0" y="0" width={CHART_WIDTH} height={CHART_HEIGHT} rx="24" fill="#0b1120" />

          {horizontalTicks.map((tick) => (
            <g key={tick.y}>
              <line x1={MARGIN.left} x2={CHART_WIDTH - MARGIN.right} y1={tick.y} y2={tick.y} stroke="#243041" strokeDasharray="4 6" />
              <text x={CHART_WIDTH - MARGIN.right + 12} y={tick.y + 4} fontSize="13" fill="#9CA3AF">
                {formatNumber(tick.value, 0)}
              </text>
            </g>
          ))}

          {verticalTicks.map((tick) => (
            <g key={`${tick.x}-${tick.label}`}>
              <line x1={tick.x} x2={tick.x} y1={MARGIN.top} y2={volumeBottom} stroke="#1e293b" strokeDasharray="4 6" />
              <text x={tick.x} y={CHART_HEIGHT - 18} textAnchor="middle" fontSize="12" fill="#9CA3AF">
                {tick.label}
              </text>
            </g>
          ))}

          <line x1={MARGIN.left} x2={MARGIN.left} y1={MARGIN.top} y2={volumeBottom} stroke="#334155" strokeWidth="1.5" />
          <line x1={MARGIN.left} x2={CHART_WIDTH - MARGIN.right} y1={volumeBottom} y2={volumeBottom} stroke="#334155" strokeWidth="1.5" />

          {visiblePoints.map((point) => {
            const isUp = point.close >= point.open;
            const bodyTop = Math.min(yScale(point.open), yScale(point.close));
            const bodyHeight = Math.max(Math.abs(yScale(point.close) - yScale(point.open)), 2);
            const candleColor = isUp ? '#22C55E' : '#EF4444';
            const volumeY = volumeScale(point.volume);

            return (
              <g key={`${point.date}-${point.index}`}>
                <rect
                  x={point.x - candleWidth / 2}
                  y={volumeY}
                  width={Math.max(2, candleWidth)}
                  height={Math.max(volumeBottom - volumeY, 2)}
                  rx="2"
                  fill={isUp ? 'rgba(34,197,94,0.28)' : 'rgba(239,68,68,0.24)'}
                />
                {mode === 'candle' ? (
                  <>
                    <line x1={point.x} x2={point.x} y1={yScale(point.high)} y2={yScale(point.low)} stroke={candleColor} strokeWidth="1.5" />
                    <rect
                      x={point.x - candleWidth / 2}
                      y={bodyTop}
                      width={candleWidth}
                      height={bodyHeight}
                      rx="2"
                      fill={candleColor}
                      fillOpacity={0.88}
                    />
                  </>
                ) : null}
              </g>
            );
          })}

          {mode === 'line' ? (
            <>
              <path d={fillPath} fill="url(#tradeLineFill)" />
              <path d={closePath} fill="none" stroke="#22C55E" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
            </>
          ) : null}

          <path d={sma50Path} fill="none" stroke="#3B82F6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          <path d={sma200Path} fill="none" stroke="#F0A500" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />

          {activePoint ? (
            <>
              <line x1={activePoint.x} x2={activePoint.x} y1={MARGIN.top} y2={volumeBottom} stroke="#475569" strokeDasharray="5 5" />
              <line x1={MARGIN.left} x2={CHART_WIDTH - MARGIN.right} y1={hoverState.y} y2={hoverState.y} stroke="#475569" strokeDasharray="5 5" />
              <circle cx={activePoint.x} cy={yScale(mode === 'line' ? activePoint.close : activePoint.close)} r="4.5" fill="#0b1120" stroke="#E5E7EB" strokeWidth="1.5" />
              <rect
                x={CHART_WIDTH - MARGIN.right + 8}
                y={yScale(activePoint.close) - 12}
                width="56"
                height="24"
                rx="8"
                fill="#111827"
                stroke="#243041"
              />
              <text x={CHART_WIDTH - MARGIN.right + 36} y={yScale(activePoint.close) + 4} textAnchor="middle" fontSize="11" fill="#E5E7EB">
                {formatNumber(activePoint.close, 2)}
              </text>
              <ChartTooltip point={activePoint} x={activePoint.x} y={hoverState.y} />
            </>
          ) : null}
        </svg>
      </div>
    </div>
  );
}
