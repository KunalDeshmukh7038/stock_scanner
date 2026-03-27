import { ChartArea } from './ChartArea';
import { RightPanel } from './RightPanel';
import { SidebarLeft } from './SidebarLeft';

export function TradingLayout({ detail, history, currentPrice, watchlistItems, activeRange, onRangeChange, rangeOptions = [] }) {
  return (
    <div className="grid gap-4 xl:grid-cols-[60px_minmax(0,1fr)_340px]">
      <div className="xl:sticky xl:top-[150px] xl:self-start">
        <SidebarLeft />
      </div>
      <ChartArea history={history} activeRange={activeRange} onRangeChange={onRangeChange} rangeOptions={rangeOptions} />
      <RightPanel detail={detail} currentPrice={currentPrice} watchlistItems={watchlistItems} />
    </div>
  );
}
