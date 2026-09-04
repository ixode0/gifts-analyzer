import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Gift, bestMarket, thumbUrl, isWatched, toggleWatch } from '../api';

interface Props {
  gift: Gift;
  compared: boolean;
  compareFull: boolean;
  onCompare: () => void;
}

export default function GiftCard({ gift, compared, compareFull, onCompare }: Props) {
  const best = bestMarket(gift);
  const spread = gift.spread_pct;
  const [watched, setWatched] = useState(isWatched(gift.slug));
  const onStar = () => {
    const w = toggleWatch(gift);
    setWatched(w.some((x) => x.slug === gift.slug));
  };
  return (
    <div className="card">
      <div className="card-top">
        <div className="card-id">
          <img className="thumb" src={thumbUrl(gift.thumb)} alt="" loading="lazy" decoding="async" width={46} height={46} onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
          <div>
            <h3 className="card-title">{gift.name}</h3>
            <div className="card-slug">{gift.slug}</div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <button
            title="В вотчлист"
            onClick={onStar}
            style={{ background: 'none', border: 0, cursor: 'pointer', fontSize: 17, color: watched ? '#fbbf24' : '#52525b', padding: 2 }}
          >{watched ? '★' : '☆'}</button>
          {best && <span className="badge violet">{best}</span>}
        </div>
      </div>
      <div className="rows">
        {gift.fragment_floor != null && (
          <div className="rowline"><span className="k">Fragment floor</span><span className="mono">{gift.fragment_floor} TON</span></div>
        )}
        <div className="rowline"><span className="k">Portals floor</span><span className="mono">{gift.portals_floor ?? '—'}{gift.portals_floor != null ? ' TON' : ''}</span></div>
        <div className="rowline"><span className="k">Tonnel floor</span><span className="mono">{gift.tonnel_floor ?? '—'}{gift.tonnel_floor != null ? ' TON' : ''}</span></div>
        <div className="rowline">
          <span className="k">Spread</span>
          {spread != null ? (
            <span className={spread > 0 ? 'up mono' : spread < 0 ? 'down mono' : 'mono'}>{spread > 0 ? '+' : ''}{spread}%</span>
          ) : <span className="mono">—</span>}
        </div>
      </div>
      <div className="card-actions">
        <Link className="btn primary" to={`/gift/${encodeURIComponent(gift.slug)}`}>Details</Link>
        <button className="btn" disabled={!compared && compareFull} onClick={onCompare}>
          {compared ? '✓ Comparing' : 'Compare'}
        </button>
      </div>
    </div>
  );
}
