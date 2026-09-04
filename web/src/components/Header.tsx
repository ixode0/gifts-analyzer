import { NavLink } from 'react-router-dom';

export default function Header({ updated }: { updated: string }) {
  return (
    <header className="header">
      <div className="header-inner">
        <NavLink to="/" className="logo">
          <svg width="26" height="26" viewBox="0 0 28 28" fill="none" aria-hidden>
            <rect x="1" y="1" width="26" height="26" rx="7" fill="url(#lg)" />
            <path d="M6 19.5 11 14l3.2 3.2L21.5 9.5" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="21.5" cy="9.5" r="2" fill="#fff" />
            <defs>
              <linearGradient id="lg" x1="1" y1="1" x2="27" y2="27">
                <stop stopColor="#8b5cf6" />
                <stop offset="1" stopColor="#34d399" />
              </linearGradient>
            </defs>
          </svg>
          <span className="logo-text">GiftScope</span>
        </NavLink>
        <nav className="nav">
          <NavLink to="/" className={({ isActive }) => (isActive ? 'active' : '')}>Gifts</NavLink>
          <NavLink to="/deals" className={({ isActive }) => (isActive ? 'active' : '')}>Deals</NavLink>
          <NavLink to="/arbitrage" className={({ isActive }) => (isActive ? 'active' : '')}>Arbitrage</NavLink>
          <NavLink to="/top" className={({ isActive }) => (isActive ? 'active' : '')}>Rankings</NavLink>
          <NavLink to="/watchlist" className={({ isActive }) => (isActive ? 'active' : '')}>Watchlist</NavLink>
        </nav>
        <div className="live"><span className="dot" />live · {updated || '—'}</div>
      </div>
    </header>
  );
}
