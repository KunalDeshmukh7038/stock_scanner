export function Footer() {
  return (
    <footer className="border-t border-white/10 bg-[#08101c]/90">
      <div className="mx-auto grid max-w-[1480px] gap-6 px-4 py-8 text-sm text-muted sm:px-6 lg:grid-cols-[1.2fr_0.8fr_0.8fr] lg:px-8">
        <div>
          <div className="font-display text-lg font-bold text-white">Sentimental Drive</div>
          <p className="mt-3 max-w-xl leading-7">
            Sentiment-driven stock prediction workspace built for NIFTY 100 research, combining technical indicators, AI direction, and live market context.
          </p>
        </div>
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-muted/80">Stack</div>
          <p className="mt-3 leading-7">React, Tailwind CSS, FastAPI, technical indicators, sentiment scoring, and market data integrations.</p>
        </div>
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-muted/80">Focus</div>
          <p className="mt-3 leading-7">A cleaner portfolio-ready interface for screening, detail analysis, and model-backed stock discovery.</p>
        </div>
      </div>
    </footer>
  );
}
