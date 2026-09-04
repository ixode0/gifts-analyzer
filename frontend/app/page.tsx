'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';

const API = process.env.NEXT_PUBLIC_API || 'http://localhost:8000';

type Row = {
  slug: string; name: string;
  portals_floor: number | null; tonnel_floor: number | null;
  spread_pct: number | null; ton_rate: number; ts: number;
};

export default function Home() {
  const [rows, setRows] = useState<Row[]>([]);
  const [q, setQ] = useState('');
  const [empty, setEmpty] = useState(false);

  async function load() {
    const r = await fetch(`${API}/api/collections`);
    const j = await r.json();
    setRows(j.data || []);
    setEmpty(!!j.empty);
  }
  useEffect(() => { load(); const t = setInterval(load, 180000); return () => clearInterval(t); }, []);

  const f = rows.filter(r => (r.name + r.slug).toLowerCase().includes(q.toLowerCase()));

  return (
    <main>
      <h1>🎁 Gifts Analyzer <span style={{ fontSize: 14, color: '#8b949e' }}>Portals + Tonnel · обновл. 3 мин</span></h1>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="поиск подарка..."
          style={{ flex: 1, padding: 8, borderRadius: 8, border: '1px solid #30363d', background: '#161b22', color: '#fff' }} />
        <button onClick={load} style={{ padding: '8px 14px', borderRadius: 8 }}>↻</button>
        <Link href="#top" style={{ padding: '8px 14px', borderRadius: 8, background: '#238636', color: '#fff', textDecoration: 'none' }}>топ</Link>
      </div>
      {empty && <p>БД пуста. Запусти бэк и нажми: <code>curl -X POST {API}/api/poll</code></p>}
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
        <thead><tr style={{ color: '#8b949e', textAlign: 'left' }}>
          <th>Подарок</th><th>Portals (TON)</th><th>Tonnel (TON)</th><th>Спред</th><th></th>
        </tr></thead>
        <tbody>
          {f.map(r => (
            <tr key={r.slug} style={{ borderTop: '1px solid #21262d' }}>
              <td style={{ padding: '8px 4px' }}><b>{r.name}</b><br /><span style={{ color: '#8b949e' }}>{r.slug}</span></td>
              <td>{r.portals_floor ?? '—'}</td>
              <td>{r.tonnel_floor ?? '—'}</td>
              <td style={{ color: r.spread_pct && r.spread_pct > 0 ? '#3fb950' : '#f85149' }}>{r.spread_pct != null ? `${r.spread_pct}%` : '—'}</td>
              <td><Link href={`/gift/${r.slug}`} style={{ color: '#58a6ff' }}>график →</Link></td>
            </tr>
          ))}
        </tbody>
      </table>
      {!f.length && !empty && <p style={{ color: '#8b949e' }}>Загрузка...</p>}
    </main>
  );
}
