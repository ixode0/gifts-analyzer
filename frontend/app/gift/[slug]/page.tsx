'use client';
import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import Link from 'next/link';

const API = process.env.NEXT_PUBLIC_API || 'http://localhost:8000';

export default function GiftPage({ params }: { params: { slug: string } }) {
  const slug = decodeURIComponent(params.slug);
  const [days, setDays] = useState(7);
  const [data, setData] = useState<any[]>([]);

  async function load(d: number) {
    const r = await fetch(`${API}/api/history?slug=${encodeURIComponent(slug)}&days=${d}`);
    const j = await r.json();
    setData((j.data || []).map((p: any) => ({
      ...p,
      time: new Date(p.ts * 1000).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }),
    })));
  }
  useEffect(() => { load(days); }, [slug]);

  const last = data[data.length - 1];

  return (
    <main>
      <Link href="/" style={{ color: '#58a6ff' }}>← все подарки</Link>
      <h1>{last?.name || slug}</h1>
      {last && <p>Portals: <b>{last.portals_floor ?? '—'} TON</b> · Tonnel: <b>{last.tonnel_floor ?? '—'} TON</b>
        {last.ton_rate ? <span style={{ color: '#8b949e' }}> · TON ${last.ton_rate}</span> : null}</p>}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        {[1, 7, 30].map(d => (
          <button key={d} onClick={() => { setDays(d); load(d); }}
            style={{ padding: '6px 12px', borderRadius: 8, background: days === d ? '#238636' : '#21262d', color: '#fff', border: 0 }}>
            {d === 1 ? '24ч' : d === 7 ? '7д' : '30д'}</button>
        ))}
      </div>
      <div style={{ background: '#161b22', borderRadius: 12, padding: 12, height: 380 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid stroke="#21262d" />
            <XAxis dataKey="time" tick={{ fill: '#8b949e', fontSize: 11 }} minTickGap={40} />
            <YAxis tick={{ fill: '#8b949e', fontSize: 11 }} domain={['auto', 'auto']} />
            <Tooltip contentStyle={{ background: '#0d1117', border: '1px solid #30363d' }} />
            <Line type="monotone" dataKey="portals_floor" name="Portals" stroke="#58a6ff" dot={false} strokeWidth={2} />
            <Line type="monotone" dataKey="tonnel_floor" name="Tonnel" stroke="#3fb950" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      {!data.length && <p style={{ color: '#8b949e' }}>Пока нет истории — поллер копит каждые 3 мин. Бэкфилл: /api/history-remote</p>}
    </main>
  );
}
