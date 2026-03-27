import { useEffect } from 'react';
import { Route, Routes, useLocation } from 'react-router-dom';

import { Footer } from './components/Footer';
import { Navbar } from './components/Navbar';
import { HomePage } from './pages/HomePage';
import { ScreenerPage } from './pages/ScreenerPage';
import { StockDetailPage } from './pages/StockDetailPage';

function ScrollToTop() {
  const location = useLocation();

  useEffect(() => {
    if (location.hash) {
      const element = document.querySelector(location.hash);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
      }
    }

    window.scrollTo({ top: 0, behavior: 'auto' });
  }, [location.pathname, location.hash]);

  return null;
}

export default function App() {
  return (
    <div className="min-h-screen bg-transparent text-ink">
      <ScrollToTop />
      <Navbar />
      <main className="mx-auto min-h-[calc(100vh-172px)] max-w-[1480px] px-4 py-8 sm:px-6 lg:px-8 lg:py-10">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/screener" element={<ScreenerPage />} />
          <Route path="/stocks/:symbol" element={<StockDetailPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
