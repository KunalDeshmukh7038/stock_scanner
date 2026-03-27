import { ChartNoAxesCombined, UserRound } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

export function Navbar() {
  const location = useLocation();

    return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-[#05070d]/78 backdrop-blur-2xl">
      <div className="mx-auto flex max-w-[1480px] items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <Link to="/" className="group flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-[1.1rem] border border-white/10 bg-gradient-to-br from-[#111827] to-[#172033] text-[#3B82F6] shadow-[0_14px_30px_rgba(2,6,23,0.35)] transition duration-300 group-hover:scale-[1.03] group-hover:border-[#3B82F6]/40">
            <ChartNoAxesCombined className="h-5 w-5" />
          </div>
          <div>
            <div className="font-display text-lg font-bold tracking-tight text-white">
              Sentimental Drive
            </div>
            <div className="text-xs text-muted">AI stock intelligence for NIFTY 100</div>
          </div>
        </Link>

        <div className="flex items-center gap-3">
          <Link
            to="/"
            className={`rounded-full border px-5 py-3 text-sm font-medium transition duration-300 sm:inline-flex sm:items-center ${
              location.pathname === '/'
                ? 'border-[#3B82F6]/35 bg-[#3B82F6]/15 text-white shadow-[0_12px_30px_rgba(59,130,246,0.16)]'
                : 'border-white/10 bg-white/[0.03] text-muted hover:border-white/20 hover:bg-white/[0.06] hover:text-white'
            }`}
          >
            Home
          </Link>
          <button className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2.5 text-sm font-semibold text-white shadow-soft transition duration-300 hover:border-white/20 hover:bg-white/[0.08]">
            <UserRound className="h-4 w-4" />
            Login
          </button>
        </div>
      </div>
    </header>
  );
}
