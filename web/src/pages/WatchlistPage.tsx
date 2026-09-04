import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, getWatch, toggleWatch, Gift } from '../api';

export default function WatchlistPage() {
  const [watched, setWatched] = useState(getWatch());
  const [prices, setPrices] = useState<Record<string, Gift>>({});
  const [notif, setNotif] = useState(typeof Notification !== 'undefined' ? Notification.permission : 'denied');
  const [fired, setFired] = useState<Record<string, boolean>>({});

  useEffect(() => {
    api.collections().then((j) => {
      const m: Record<string, Gift> = {};
      (j.data || []).forEach((g) => { m[g.slug] = g; });
      setPrices(m);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (notif !== 'granted') return;
    watched.forEach((w) => {
      const g = prices[w.slug];
      if (!g?.min_floor || !w.price) return;
      const drop = (1 - g.min_floor / w.price) * 100;
      if (drop >= 5 && !fired[w.slug]) {
        setFired((p) => ({ ...p, [w.slug]: true }));
        try {
          new Notification(`${w.name}: −${drop.toFixed(1)}%`, { body: `Флор ${g.min_floor} TON (было ${w.price})` });
        } catch { /* ignore */ }
      }
    });
  }, [prices, watched, notif, fired]);

  const enableNotif = async () => {
    try {
      const p = await Notification.requestPermission();
      setNotif(p);
    } catch { /* ignore */ }
  };

  const remove = (slug: string) => {
    const g = watched.find((x) => x.slug === slug);
    if (g) setWatched(toggleWatch({ slug: g.slug, name: g.name, min_floor: g.price } as Gift));
  };

  return (
    <>
      <section className="hero">
        <h1>Watchlist</h1>
        <p>Отслеживаемые подарки хранятся в браузере. Падение флора на 5%+ от цены добавления — алерт.</p>
        {notif !== 'granted' && <button className="btn primary" style={{ flex: 'none', padding: '9px 16px' }} onClick={enableNotif}>Включить уведомления</button>}
        {notif === 'granted' && <span className="badge green">notifications on</span>}
      </section>
      {!watched.length && <p className="muted">Пусто. Жми ★ на карточке подарка. <Link to="/">← Gifts</Link></p>}
      {!!watched.length && (
        <div className="table-scroll">
        <table className="tbl">
          <thead><tr><th>Gift</th><th>Watched at</th><th>Floor now</th><th>Change</th><th></th></tr></thead>
          <tbody>
            {watched.map((w) => {
              const g = prices[w.slug];
              const now = g?.min_floor;
              const chg = now && w.price ? ((now - w.price) / w.price) * 100 : null;
              return (
                <tr key={w.slug}>
                  <td><b>{w.name}</b> <span className="muted mono">{w.slug}</span></td>
                  <td className="mono">{w.price || '—'}</td>
                  <td className="mono">{now ?? '...'}</td>
                  <td className={chg != null && chg < 0 ? 'down' : chg != null && chg > 0 ? 'up' : ''}>
                    {chg != null ? `${chg > 0 ? '+' : ''}${chg.toFixed(1)}%` : '—'}
                  </td>
                  <td>
                    <Link to={`/gift/${encodeURIComponent(w.slug)}`} style={{ color: '#a78bfa' }}>chart →</Link>
                    {' '}<button className="btn" style={{ flex: 'none', padding: '4px 10px', marginLeft: 8 }} onClick={() => remove(w.slug)}>✕</button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        </div>
      )}
    </>
  );
}
