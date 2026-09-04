import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../api';

const COLORS = ['#8b5cf6', '#34d399', '#60a5fa', '#f472b6'];

export default function ComparePage({ compare, toggleCompare }: { compare: string[]; toggleCompare: (s: string) => void }) {
  const [params] = useSearchParams();
  const slugs = useMemo(() => {
    const q = params.get('slugs');
    return q ? q.split(',').map(decodeURIComponent).filter(Boolean).slice(0, 4) : compare.slice(0, 4);
  }, [params, compare]);
  const [series, setSeries] = useState<Record<string, any[]>>({});

  useEffect(() => {
    slugs.forEach(async (s) => {
      try {
        const j = await api.history(s, 7);
        setSeries((prev) => ({ ...prev, [s]: j.data || [] }));
      } catch { /* ignore */ }
    });
  }, [slugs.join(',')]);

  // merge by ts, normalize to % from first point
  const merged = useMemo(() => {
    const byTs: Record<number, any> = {};
    slugs.forEach((s) => {
      const pts = (series[s] || []).filter((p: any) => p.portals_floor).sort((a: any, b: any) => a.ts - b.ts);
      const base = pts[0]?.portals_floor;
      if (!base) return;
      pts.forEach((p: any) => {
        byTs[p.ts] = byTs[p.ts] || { ts: p.ts, time: new Date(p.ts * 1000).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) };
        byTs[p.ts][s] = +(((p.portals_floor - base) / base) * 100).toFixed(2);
      });
    });
    return Object.values(byTs).sort((a: any, b: any) => a.ts - b.ts);
  }, [series, slugs.join(',')]);

  if (!slugs.length) return <p className="muted" style={{ marginTop: 40 }}>Выбери до 4 подарков кнопкой Compare на главной. <Link to="/">← Gifts</Link></p>;

  return (
    <>
      <section className="hero">
        <h1>Compare</h1>
        <p>Нормированная динамика флора Portals, % от первой точки (7д).</p>
      </section>
      <div className="chart-wrap">
        {merged.length ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={merged}>
              <CartesianGrid stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="time" tick={{ fill: '#71717a', fontSize: 11 }} minTickGap={50} />
              <YAxis tick={{ fill: '#71717a', fontSize: 11 }} width={60} />
              <Tooltip contentStyle={{ background: '#141417', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
              <Legend />
              {slugs.map((s, i) => (
                <Line key={s} type="monotone" dataKey={s} stroke={COLORS[i % COLORS.length]} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        ) : <p className="muted">Загрузка истории...</p>}
      </div>
      <div className="section">
        {slugs.map((s) => (
          <div key={s} className="rowline" style={{ padding: '6px 0' }}>
            <span className="mono">{s}</span>
            <span><Link to={`/gift/${encodeURIComponent(s)}`} style={{ color: '#a78bfa' }}>details →</Link>
              {' '}<button className="btn" style={{ flex: 'none', padding: '4px 10px', marginLeft: 8 }} onClick={() => toggleCompare(s)}>remove</button></span>
          </div>
        ))}
      </div>
    </>
  );
}
