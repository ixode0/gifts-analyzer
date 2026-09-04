import { useState } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Header from './components/Header';
import Home from './pages/Home';
import GiftPage from './pages/GiftPage';
import TopPage from './pages/TopPage';
import ComparePage from './pages/ComparePage';
import DealsPage from './pages/DealsPage';
import ArbitragePage from './pages/ArbitragePage';
import WatchlistPage from './pages/WatchlistPage';

export default function App() {
  const [compare, setCompare] = useState<string[]>([]);
  const toggleCompare = (slug: string) =>
    setCompare((prev) => (prev.includes(slug) ? prev.filter((s) => s !== slug) : prev.length >= 4 ? prev : [...prev, slug]));

  return (
    <BrowserRouter>
      <Header updated="3m refresh" />
      <div className="container">
        <Routes>
          <Route path="/" element={<Home compare={compare} toggleCompare={toggleCompare} />} />
          <Route path="/gift/:slug" element={<GiftPage />} />
          <Route path="/top" element={<TopPage />} />
          <Route path="/deals" element={<DealsPage />} />
          <Route path="/arbitrage" element={<ArbitragePage />} />
          <Route path="/watchlist" element={<WatchlistPage />} />
          <Route path="/compare" element={<ComparePage compare={compare} toggleCompare={toggleCompare} />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
