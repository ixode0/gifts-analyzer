import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, Gift } from '../api';
import GiftCard from '../components/GiftCard';

type SortKey = 'price-desc' | 'price-asc' | 'spread-desc' | 'name';

export default function Home({ compare, toggleCompare }: { compare: string[]; toggleCompare: (s: string) => void }) {
  const [gifts, setGifts] = useState<Gift[]>([]);
  const [q, setQ] = useState('');
  const [market, setMarket] = useState<'all' | 'portals' | 'tonnel' | 'fragment'>('all');
  const [sort, setSort] = useState<SortKey>('price-desc');
  const [updated, setUpdated] = useState('');

  async function load() {
    try {
      const j = await api.collections();
      setGifts(j.data || []);
      const ts = j.data?.[0]?.ts;
      if (ts) setUpdated(new Date(ts * 1000).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }));
    } catch { /* poller копит данные */ }
  }
  useEffect(() => {
    load();
    const t = setInterval(load, 180000);
    return () => clearInterval(t);
  }, []);

  const floor = (g: Gift) =>
    market === 'tonnel' ? g.tonnel_floor
    : market === 'portals' ? g.portals_floor
    : market === 'fragment' ? g.fragment_floor
    : g.min_floor;

  const list = useMemo(() => {
    let r = gifts.filter((g) => (g.name + g.slug).toLowerCase().includes(q.toLowerCase()));
    if (market !== 'all') r = r.filter((g) => floor(g) != null);
    const val = (g: Gift) => floor(g) ?? -1;
    r = [...r].sort((a, b) => {
      if (sort === 'price-desc') return val(b) - val(a);
      if (sort === 'price-asc') return val(a) - val(b);
      if (sort === 'spread-desc') return (b.spread_pct ?? -999) - (a.spread_pct ?? -999);
      return a.name.localeCompare(b.name);
    });
    return r;
  }, [gifts, q, market, sort]);

  const priced = gifts.filter((g) => g.min_floor != null);
  const avg = priced.length ? priced.reduce((s, g) => s + (g.min_floor ?? 0), 0) / priced.length : 0;

  return (
    <>
      <section className="hero">
        <h1>Gifts</h1>
        <p>Флор каждого подарка: Fragment + Portals и Tonnel (когда доступен Giftstat). Обновление каждые 3 мин.</p>
        <div className="stats">
          <div className="stat"><div className="k">Tracked gifts</div><div className="v">{gifts.length}</div></div>
          <div className="stat"><div className="k">Avg floor (TON)</div><div className="v">{avg ? avg.toFixed(1) : '—'}</div></div>
          <div className="stat"><div className="k">Markets</div><div className="v">3</div></div>
          <div className="stat"><div className="k">Updated</div><div className="v" style={{ fontSize: 17 }}>{updated || '—'}</div></div>
        </div>
      </section>

      <div className="toolbar">
        <div className="search">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></svg>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search gifts..." />
        </div>
        <div className="pills">
          {(['all', 'portals', 'tonnel', 'fragment'] as const).map((m) => (
            <button key={m} className={market === m ? 'pill active' : 'pill'} onClick={() => setMarket(m)}>
              {m === 'all' ? 'All' : m === 'portals' ? 'Portals' : m === 'tonnel' ? 'Tonnel' : 'Fragment'}
            </button>
          ))}
        </div>
        <select className="sort" value={sort} onChange={(e) => setSort(e.target.value as SortKey)}>
          <option value="price-desc">Price: high → low</option>
          <option value="price-asc">Price: low → high</option>
          <option value="spread-desc">Spread: max</option>
          <option value="name">Name A–Z</option>
        </select>
      </div>

      {!gifts.length && <p className="muted">Загрузка... Если пусто дольше минуты — поллер еще копит первый снимок (POST /api/poll).</p>}
      <div className="grid">
        {list.map((g) => (
          <GiftCard key={g.slug} gift={g} compared={compare.includes(g.slug)} compareFull={compare.length >= 4} onCompare={() => toggleCompare(g.slug)} />
        ))}
      </div>

      {compare.length > 0 && (
        <div className="compare-bar">
          <span>Selected: <b>{compare.length}</b>/4</span>
          <Link className="btn primary" to={`/compare?slugs=${compare.map(encodeURIComponent).join(',')}`}>Open compare →</Link>
        </div>
      )}
    </>
  );
}
