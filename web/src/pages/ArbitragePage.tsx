import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, Arb } from '../api';

export default function ArbitragePage() {
  const [rows, setRows] = useState<Arb[]>([]);
  const [fees, setFees] = useState<Record<string, number>>({});

  useEffect(() => {
    api.arbitrage().then((j) => { setRows(j.data || []); setFees(j.fees || {}); }).catch(() => {});
  }, []);

  return (
    <>
      <section className="hero">
        <h1>Arbitrage</h1>
        <p>Спреды между маркетами уже NET — с вычетом комиссий тейкера: {Object.entries(fees).map(([m, f]) => `${m} ${(f * 100).toFixed(0)}%`).join(' · ')}. Показан профит от 2%.</p>
      </section>
      {!rows.length && <p className="muted">Нет прибыльных связок прямо сейчас (или ждем больше маркетов — Portals подтянется с Giftstat).</p>}
      {!!rows.length && (
        <table className="tbl">
          <thead><tr><th>Gift</th><th>Buy</th><th>Sell</th><th>Net TON</th><th>Net %</th><th></th></tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={`${r.slug}-${r.buy_market}-${r.sell_market}-${i}`}>
                <td><b>{r.name}</b> <span className="muted mono">{r.slug}</span></td>
                <td className="mono">{r.buy_market} · {r.buy_price}</td>
                <td className="mono">{r.sell_market} · {r.sell_price}</td>
                <td className="mono up">+{r.net_ton}</td>
                <td className="up">+{r.net_pct}%</td>
                <td><Link to={`/gift/${encodeURIComponent(r.slug)}`} style={{ color: '#a78bfa' }}>chart →</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
