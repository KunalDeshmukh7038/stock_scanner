import { Activity, ChartCandlestick, MousePointer2, PenTool, Ruler, ScanLine, Type } from 'lucide-react';

const toolIcons = [
  { id: 'cursor', icon: MousePointer2, label: 'Cursor' },
  { id: 'trend', icon: ChartCandlestick, label: 'Trend' },
  { id: 'draw', icon: PenTool, label: 'Drawing' },
  { id: 'measure', icon: Ruler, label: 'Measure' },
  { id: 'text', icon: Type, label: 'Text' },
  { id: 'indicator', icon: Activity, label: 'Indicator' },
  { id: 'scan', icon: ScanLine, label: 'Scanner' },
];

export function SidebarLeft() {
  return (
    <aside className="flex h-full w-[60px] flex-col items-center gap-3 rounded-[1.35rem] border border-white/10 bg-[#111827]/92 px-2 py-4 shadow-[0_22px_40px_rgba(2,6,23,0.35)] backdrop-blur-xl">
      {toolIcons.map(({ id, icon: Icon, label }, index) => (
        <button
          key={id}
          type="button"
          title={label}
          className={`inline-flex h-10 w-10 items-center justify-center rounded-xl border transition duration-200 ${
            index === 0
              ? 'border-[#3B82F6]/40 bg-[#3B82F6]/16 text-white shadow-[0_10px_24px_rgba(59,130,246,0.18)]'
              : 'border-white/8 bg-white/[0.03] text-[#9CA3AF] hover:border-white/20 hover:bg-white/[0.07] hover:text-white'
          }`}
        >
          <Icon className="h-4.5 w-4.5" />
        </button>
      ))}
    </aside>
  );
}
