export const DEFAULTS = {repo: 'werti4/uniqlo-alert', branch: 'main', token: '', key: ''};
export const MAX_FAVORITES = 50;
export const AAD = new TextEncoder().encode('uniqlo-alert:v1');
export function b64(bytes) {
  // State can contain histories for 50 products. Avoid spreading it onto the JS stack.
  let raw = '';
  for (let start = 0; start < bytes.length; start += 8192) raw += String.fromCharCode(...bytes.subarray(start, start + 8192));
  return btoa(raw).replaceAll('+', '-').replaceAll('/', '_').replaceAll('=', '');
}
export function unb64(text) {
  if (typeof text !== 'string' || !/^[A-Za-z0-9_-]+$/.test(text) || text.length % 4 === 1) throw new Error('Encodage chiffré invalide.');
  return Uint8Array.from(atob(text.replaceAll('-', '+').replaceAll('_', '/') + '='.repeat((4 - text.length % 4) % 4)), c => c.charCodeAt(0));
}
export function newKey() { return b64(crypto.getRandomValues(new Uint8Array(32))); }
async function aes(key, usage) {
  if (!key || unb64(key).length !== 32) throw new Error('La clé de chiffrement doit contenir 32 octets.');
  return crypto.subtle.importKey('raw', unb64(key), 'AES-GCM', false, [usage]);
}
export async function seal(value, key) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const payload = await crypto.subtle.encrypt({name: 'AES-GCM', iv, additionalData: AAD}, await aes(key, 'encrypt'), new TextEncoder().encode(JSON.stringify(value)));
  return {v: 1, alg: 'A256GCM', iv: b64(iv), data: b64(new Uint8Array(payload))};
}
export async function unseal(value, key) {
  if (!value || value.v !== 1 || value.alg !== 'A256GCM') throw new Error('Format chiffré inconnu.');
  try {
    if (unb64(value.iv).length !== 12) throw new Error('Nonce invalide.');
    const bytes = await crypto.subtle.decrypt({name: 'AES-GCM', iv: unb64(value.iv), additionalData: AAD}, await aes(key, 'decrypt'), unb64(value.data));
    return JSON.parse(new TextDecoder().decode(bytes));
  } catch { throw new Error('La clé ne correspond pas aux données distantes. Aucune donnée remplacée.'); }
}
export function canonical(raw) {
  let u;
  try { u = new URL(raw); } catch { throw new Error('Colle une URL complète de fiche UNIQLO France.'); }
  const m = u.pathname.match(/^\/fr\/fr\/products\/(E\d{6}-\d{3})\/(\d{2})\/?$/);
  if (u.protocol !== 'https:' || u.host !== 'www.uniqlo.com' || u.username || u.password || !m) throw new Error('Une fiche produit UNIQLO France est requise.');
  return {id: `${m[1]}-${m[2]}`, url: u.origin + u.pathname.replace(/\/$/, '')};
}
export function money(cents) {
  return Number.isSafeInteger(cents) && cents >= 0 ? new Intl.NumberFormat('fr-FR', {style: 'currency', currency: 'EUR'}).format(cents / 100) : '—';
}
export function relative(date) {
  if (!date) return 'Pas encore vérifié';
  if (!Number.isFinite(new Date(date).getTime())) return 'Date indisponible';
  const n = Math.max(0, Math.round((Date.now() - new Date(date).getTime()) / 60000));
  if (n < 1) return 'À l’instant';
  if (n < 60) return `Il y a ${n} min`;
  if (n < 1440) return `Il y a ${Math.floor(n / 60)} h`;
  return new Date(date).toLocaleDateString('fr-FR');
}

const text = (value, limit = 200) => typeof value === 'string' ? value.slice(0, limit) : '';
const validPrice = value => Number.isSafeInteger(value) && value > 0 && value < 10_000_000;
export function safeImage(value) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && url.host === 'image.uniqlo.com' && !url.username && !url.password ? url.href : null;
  } catch { return null; }
}
export function normalizeFavorites(value) {
  if (!Array.isArray(value) || value.length > MAX_FAVORITES) throw new Error('Liste distante invalide : 50 favoris maximum. Aucune donnée locale remplacée.');
  const ids = new Set();
  return value.map(f => {
    if (!f || typeof f !== 'object') throw new Error('Favori distant invalide. Aucune donnée locale remplacée.');
    const parsed = canonical(f.url);
    if (f.id !== parsed.id || ids.has(parsed.id)) throw new Error('Références distantes invalides ou en double. Aucune donnée locale remplacée.');
    if (typeof f.enabled !== 'boolean') throw new Error('Statut de favori distant invalide. Aucune donnée locale remplacée.');
    if (f.targetCents != null && !validPrice(f.targetCents)) throw new Error('Objectif distant invalide. Aucune donnée locale remplacée.');
    ids.add(parsed.id);
    return {...parsed, name: text(f.name) || 'Article UNIQLO', image: safeImage(f.image),
      color: text(f.color, 80), size: text(f.size, 40), enabled: f.enabled !== false,
      targetCents: f.targetCents ?? null, ...(typeof f.addedAt === 'string' ? {addedAt: f.addedAt} : {})};
  });
}
export function normalizeWatchlist(value) {
  if (!value || value.schema !== 1) throw new Error('Version de favoris distante inconnue. Aucune donnée locale remplacée.');
  return {...value, favorites: normalizeFavorites(value.favorites)};
}
export function normalizeCloud(value) {
  const bad = () => { throw new Error('Historique distant invalide. Le dernier relevé local est conservé.'); };
  if (!value || value.schema !== 1 || !value.products || typeof value.products !== 'object' || Array.isArray(value.products) || !Array.isArray(value.alerts)) bad();
  const products = {};
  for (const [id, p] of Object.entries(value.products)) {
    if (!/^E\d{6}-\d{3}-\d{2}$/.test(id) || !p || typeof p !== 'object') bad();
    if (p.id != null && p.id !== id) bad();
    for (const key of ['priceCents', 'regularCents', 'firstPriceCents', 'lowestCents']) if (p[key] != null && !validPrice(p[key])) bad();
    if (p.url && canonical(p.url).id !== id) bad();
    if (p.history != null && (!Array.isArray(p.history) || p.history.some(h => !h || !validPrice(h.priceCents) || !Number.isFinite(Date.parse(h.at))))) bad();
    products[id] = {...p, id, ...(p.name ? {name: text(p.name)} : {}), image: safeImage(p.image),
      sizes: Array.isArray(p.sizes) ? p.sizes.filter(s => typeof s === 'string').slice(0, 100) : [],
      history: (p.history || []).slice(-120)};
  }
  const alerts = value.alerts.map(e => {
    if (!e || !validPrice(e.oldCents) || !validPrice(e.newCents) || e.newCents >= e.oldCents || !Number.isFinite(Date.parse(e.at))) bad();
    const parsed = canonical(e.url);
    if (e.productId !== parsed.id || !['sent', 'pending'].includes(e.delivery)) bad();
    return {...e, name: text(e.name) || 'Article UNIQLO', url: parsed.url};
  });
  return {...value, products, alerts};
}
export function validBranch(branch) {
  return typeof branch === 'string' && /^[A-Za-z0-9][A-Za-z0-9_./-]{0,199}$/.test(branch) &&
    !branch.includes('..') && !branch.includes('//') && !branch.endsWith('/') && !branch.endsWith('.') &&
    !branch.split('/').some(part => part.startsWith('.') || part.endsWith('.lock'));
}
