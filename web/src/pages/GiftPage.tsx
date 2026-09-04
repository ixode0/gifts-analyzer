import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api, HistPoint } from '../api';

const PERIODS = [{ d: 1, label: '24H' }, { d: 7, label: '7D' }, { d: 30, label: '30D' }];

export default function GiftPage() {
  const { slug = '' } = useParams();
  const name = decodeURIComponent(slug);
  const [days, setDays] = useState(7);
  const [data, setData] = useState<HistPoint[]>([]);

  async function load(d: number) {
    try {
      const j = await api.history(name, d);
      setData(j.data || []);
    } catch { setData([]); }
  }
  useEffect(() => { load(days); }, [name]);

  const chart = useMemo(
    () => data.map((p) => ({
      ...p,
      time: new Date(p.ts * 1000).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }),
    })),
    [data]
  );
  const last = data[data.length - 1];
  const first = data[0];
  const chg = last && first?.portals_floor && last.portals_floor
    ? (((last.portals_floor - first.portals_floor) / first.portals_floor) * 100).toFixed(2) : null;

  return (
    <>
      <div className="detail-head">
        <Link className="back" to="/">← All gifts</Link>
        <h1>{last?.name || name}</h1>
        <div className="muted mono">{name}</div>
      </div>
      {last && (
        <div className="price-line">
          {(last as any).fragment_floor != null && <div className="price-box"><div className="k">Fragment floor</div><div className="v">{(last as any).fragment_floor} <span style={{ fontSize: 13 }}>TON</span></div></div>}
          <div className="price-box"><div className="k">Portals floor</div><div className="v">{last.portals_floor ?? '—'} <span style={{ fontSize: 13 }}>TON</span></div></div>
          <div className="price-box"><div className="k">Tonnel floor</div><div className="v">{last.tonnel_floor ?? '—'} <span style={{ fontSize: 13 }}>TON</span></div></div>
          <div className="price-box"><div className="k">Change ({days === 1 ? '24h' : `${days}d`})</div>
            <div className={Number(chg) >= 0 ? 'v up' : 'v down'}>{chg != null ? `${Number(chg) > 0 ? '+' : ''}${chg}%` : '—'}</div></div>
          {last.ton_rate ? <div className="price-box"><div className="k">TON rate</div><div className="v">${last.ton_rate}</div></div> : null}
        </div>
      )}
      <div className="periods">
        {PERIODS.map((p) => (
          <button key={p.d} className={days === p.d ? 'pill active' : 'pill'} onClick={() => { setDays(p.d); load(p.d); }}>{p.label}</button>
        ))}
      </div>
      <div className="chart-wrap">
        {chart.length ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chart}>
              <defs>
                <linearGradient id="gp" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gt" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#34d399" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#34d399" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gf" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#60a5fa" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#60a5fa" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="time" tick={{ fill: '#71717a', fontSize: 11 }} minTickGap={50} />
              <YAxis tick={{ fill: '#71717a', fontSize: 11 }} domain={['auto', 'auto']} width={60} />
              <Tooltip contentStyle={{ background: '#141417', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
              <Area type="monotone" dataKey="fragment_floor" name="Fragment" stroke="#60a5fa" fill="url(#gf)" strokeWidth={2} dot={false} />
              <Area type="monotone" dataKey="portals_floor" name="Portals" stroke="#8b5cf6" fill="url(#gp)" strokeWidth={2} dot={false} />
              <Area type="monotone" dataKey="tonnel_floor" name="Tonnel" stroke="#34d399" fill="url(#gt)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        ) : <p className="muted">История копится поллером каждые 3 мин. Загляни позже.</p>}
      </div>
    </>
  );
}
