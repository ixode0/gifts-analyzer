import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, Deal, thumbUrl } from '../api';

export default function DealsPage() {
  const [deals, setDeals] = useState<Deal[]>([]);

  useEffect(() => {
    api.deals().then((j) => setDeals(j.data || [])).catch(() => {});
  }, []);

  return (
    <>
      <section className="hero">
        <h1>Deals</h1>
        <p>Недооцененные лоты Tonnel: разрыв с 2-й ценой модели (gap) и цены ниже флора Fragment (xfloor). Обновляется раз в час.</p>
      </section>
      {!deals.length && <p className="muted">Считаю сделки... первый проход занимает несколько минут.</p>}
      <div className="grid">
        {deals.map((d, i) => (
          <div className="card" key={`${d.name}-${d.gift_num}-${i}`}>
            <div className="card-top">
              <div className="card-id">
                {d.slug && <img className="thumb" src={thumbUrl(`/static/img/${d.slug}.jpg`)} alt="" loading="lazy" decoding="async" width={46} height={46} onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />}
                <div>
                  <h3 className="card-title">{d.name} #{d.gift_num ?? '—'}</h3>
                  <div className="card-slug">{d.model}{d.model_rarity != null ? ` (${d.model_rarity}%)` : ''}</div>
                </div>
              </div>
              <span className="badge green">−{d.discount_pct}%</span>
            </div>
            <div className="rows">
              <div className="rowline"><span className="k">Price</span><span className="mono"><b>{d.price} TON</b></span></div>
              <div className="rowline"><span className="k">{d.kind === 'gap' ? '2nd cheapest' : 'Fragment floor'}</span><span className="mono">{d.ref_price} TON</span></div>
              <div className="rowline"><span className="k">Signal</span><span className="badge">{d.kind}</span></div>
            </div>
            <div className="card-actions">
              <a className="btn primary" href="https://market.tonnel.network/" target="_blank" rel="noreferrer">Open Tonnel →</a>
              {d.slug && <Link className="btn" to={`/gift/${encodeURIComponent(d.slug)}`}>Chart</Link>}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
