export const API = (import.meta as any).env?.VITE_API_URL || 'http://127.0.0.1:8001';

export interface Gift {
  slug: string;
  name: string;
  portals_floor: number | null;
  tonnel_floor: number | null;
  fragment_floor: number | null;
  mrkt_floor: number | null;
  getgems_floor: number | null;
  min_floor: number | null;
  spread_pct: number | null;
  thumb: string;
  ton_rate: number;
  ts: number;
}

export interface HistPoint {
  slug: string;
  name: string;
  portals_floor: number | null;
  tonnel_floor: number | null;
  fragment_floor?: number | null;
  mrkt_floor?: number | null;
  getgems_floor?: number | null;
  ton_rate: number;
  ts: number;
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${API}${path}`);
  if (!r.ok) throw new Error(`API ${r.status}`);
  return r.json();
}

export const api = {
  collections: () => get<{ data: Gift[] }>('/api/collections'),
  history: (slug: string, days: number) =>
    get<{ data: HistPoint[] }>(`/api/history?slug=${encodeURIComponent(slug)}&days=${days}`),
  top: (period: '24h' | '7d' = '24h') => get<{ gainers: any[]; losers: any[] }>(`/api/top?period=${period}`),
  deals: () => get<{ data: Deal[] }>('/api/deals'),
  arbitrage: () => get<{ fees: Record<string, number>; data: Arb[] }>('/api/arbitrage'),
};

export interface Deal {
  slug: string | null;
  name: string;
  gift_num: number | null;
  model: string;
  model_rarity: number | null;
  backdrop: string;
  price: number;
  ref_price: number;
  discount_pct: number;
  kind: 'gap' | 'xfloor';
  market: string;
  thumb: string;
  ts: number;
}

export interface Arb {
  slug: string;
  name: string;
  buy_market: string;
  buy_price: number;
  sell_market: string;
  sell_price: number;
  net_ton: number;
  net_pct: number;
}

export interface Watched {
  slug: string;
  name: string;
  price: number;
  ts: number;
}

const WKEY = 'gs_watch_v1';

export function getWatch(): Watched[] {
  try {
    return JSON.parse(localStorage.getItem(WKEY) || '[]');
  } catch {
    return [];
  }
}

export function toggleWatch(g: Gift): Watched[] {
  const w = getWatch();
  const i = w.findIndex((x) => x.slug === g.slug);
  if (i >= 0) w.splice(i, 1);
  else w.push({ slug: g.slug, name: g.name, price: g.min_floor ?? 0, ts: Date.now() });
  localStorage.setItem(WKEY, JSON.stringify(w));
  return w;
}

export function isWatched(slug: string): boolean {
  return getWatch().some((x) => x.slug === slug);
}

export function thumbUrl(src: string): string {
  if (!src) return src;
  if (src.startsWith('http')) return src;
  return `${API}${src}`;
}

export function bestMarket(g: Gift): string | null {
  const c: [string, number | null][] = [
    ['Portals', g.portals_floor], ['Tonnel', g.tonnel_floor], ['Fragment', g.fragment_floor],
    ['MRKT', (g as any).mrkt_floor ?? null], ['GetGems', (g as any).getgems_floor ?? null],
  ];
  const avail = c.filter(([, v]) => v != null) as [string, number][];
  if (!avail.length) return null;
  return avail.sort((a, b) => a[1] - b[1])[0][0];
}

export const MARKETS: { key: keyof Gift; label: string; color: string }[] = [
  { key: 'fragment_floor', label: 'Fragment', color: '#60a5fa' },
  { key: 'portals_floor', label: 'Portals', color: '#8b5cf6' },
  { key: 'tonnel_floor', label: 'Tonnel', color: '#34d399' },
  { key: 'mrkt_floor' as keyof Gift, label: 'MRKT', color: '#fbbf24' },
  { key: 'getgems_floor' as keyof Gift, label: 'GetGems', color: '#f472b6' },
];
