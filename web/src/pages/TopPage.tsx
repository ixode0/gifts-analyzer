import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';

interface Mover { slug: string; old: number; new: number; change_pct: number; }

export default function TopPage() {
  const [period, setPeriod] = useState<'24h' | '7d'>('24h');
  const [gainers, setGainers] = useState<Mover[]>([]);
  const [losers, setLosers] = useState<Mover[]>([]);

  async function load(p: '24h' | '7d') {
    try {
      const j = await api.top(p);
      setGainers(j.gainers || []);
      setLosers(j.losers || []);
    } catch { /* empty */ }
  }
  useEffect(() => { load(period); }, [period]);

  const table = (rows: Mover[], up: boolean) => (
    <div className="table-scroll">
    <table className="tbl">
      <thead><tr><th>Gift</th><th>Old</th><th>Now</th><th>Change</th><th></th></tr></thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.slug}>
            <td className="mono">{r.slug}</td>
            <td className="mono">{r.old}</td>
            <td className="mono">{r.new}</td>
            <td className={up ? 'up' : 'down'}>{r.change_pct > 0 ? '+' : ''}{r.change_pct}%</td>
            <td><Link to={`/gift/${encodeURIComponent(r.slug)}`} style={{ color: '#a78bfa' }}>chart →</Link></td>
          </tr>
        ))}
      </tbody>
    </table>
    </div>
  );

  return (
    <>
      <section className="hero">
        <h1>Rankings</h1>
        <p>Самые подорожавшие и подешевевшие подарки по флору.</p>
        <div className="periods">
          {(['24h', '7d'] as const).map((p) => (
            <button key={p} className={period === p ? 'pill active' : 'pill'} onClick={() => { setPeriod(p); load(p); }}>{p}</button>
          ))}
        </div>
      </section>
      <div className="section"><h2>🚀 Top gainers</h2>{gainers.length ? table(gainers, true) : <p className="muted">Нужно минимум 2 снимка за период.</p>}</div>
      <div className="section"><h2>📉 Top losers</h2>{losers.length ? table(losers, false) : <p className="muted">Нужно минимум 2 снимка за период.</p>}</div>
    </>
  );
}
