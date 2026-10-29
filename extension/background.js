import {DEFAULTS, MAX_FAVORITES, canonical, newKey, seal, unseal, safeImage, normalizeWatchlist, normalizeCloud, validBranch} from './core.js';

const EMPTY_CLOUD = () => ({schema: 1, products: {}, alerts: []});
const storageReady = chrome.storage.local.setAccessLevel({accessLevel: 'TRUSTED_CONTEXTS'});
async function read() {
  await storageReady;
  const db = await chrome.storage.local.get(['settings', 'favorites', 'cloud', 'syncedAt', 'configSha', 'dirty']);
  return {...db, settings: {...DEFAULTS, ...db.settings}, favorites: db.favorites || [], cloud: db.cloud || EMPTY_CLOUD()};
}
let booting;
async function bootstrapOnce() {
  const current = await read();
  if (!current.settings.key) {
    let key;
    try {
      const response = await fetch(chrome.runtime.getURL('bootstrap.private.json'));
      if (response.ok) key = (await response.json()).key;
    } catch {}
    current.settings.key = key || newKey();
    await seal({}, current.settings.key);
    await chrome.storage.local.set({settings: current.settings});
  }
}
function bootstrap() {
  if (!booting) booting = bootstrapOnce().finally(() => { booting = null; });
  return booting;
}
chrome.runtime.onInstalled.addListener(bootstrap);
chrome.action.onClicked.addListener(async tab => {
  await bootstrap();
  const page = new URL(chrome.runtime.getURL('app.html'));
  if (tab?.id && tab.url?.startsWith('https://www.uniqlo.com/fr/fr/products/')) page.searchParams.set('source', tab.id);
  await chrome.tabs.create({url: page.href});
});

function repoPath(settings) {
  if (!/^[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+$/.test(settings.repo)) throw new Error('Indique le dépôt sous la forme compte/depot.');
  return '/repos/' + settings.repo;
}
async function api(settings, path, init = {}, missing = false) {
  if (!settings.token) throw new Error('Ajoute ton jeton GitHub dans les réglages.');
  const response = await fetch('https://api.github.com' + repoPath(settings) + path, {
    ...init, headers: {'Accept': 'application/vnd.github+json', 'Authorization': `Bearer ${settings.token}`, 'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json'},
    signal: AbortSignal.timeout(25000)
  });
  if (response.status === 404 && missing) return null;
  if (!response.ok) {
    const messages = {401: 'Jeton GitHub invalide ou expiré.', 403: 'Accès GitHub refusé : vérifie les droits Contents et Actions.', 404: 'Dépôt, branche ou workflow introuvable.', 409: 'Un changement distant existe. Actualise avant de réessayer.', 422: 'GitHub refuse cette modification. Vérifie la branche et les droits.'};
    throw new Error(messages[response.status] || `GitHub répond HTTP ${response.status}.`);
  }
  return response.status === 204 ? null : response.json();
}
function encodeContent(value) {
  const bytes = new TextEncoder().encode(JSON.stringify(value));
  // Chunk to avoid a stack overflow for larger favorite lists.
  let s = ''; for (const byte of bytes) s += String.fromCharCode(byte);
  return btoa(s);
}
function decodeContent(value) { return JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(value.replaceAll('\n', '')), c => c.charCodeAt(0)))); }
async function remoteConfig(settings) {
  const record = await api(settings, '/contents/data/watchlist.enc.json?ref=' + encodeURIComponent(settings.branch), {}, true);
  // Contents returns the same 404 for a new watchlist and an inaccessible repo/ref.
  // Verify the branch before treating that response as a successful first setup.
  if (!record) await api(settings, '/branches/' + encodeURIComponent(settings.branch));
  return record ? {sha: record.sha, value: normalizeWatchlist(await unseal(decodeContent(record.content), settings.key))} : {sha: null, value: {schema: 1, favorites: []}};
}
async function sync({replaceFavorites = false} = {}) {
  const db = await read(), remote = await remoteConfig(db.settings);
  if (!remote.sha && db.configSha) throw new Error('La liste GitHub a disparu. Les favoris locaux sont conservés. Vérifiez le dépôt avant de poursuivre.');
  if (db.dirty && !replaceFavorites && remote.sha !== (db.configSha || null)) throw new Error('Les favoris ont changé sur un autre appareil. Exporte tes favoris locaux, puis recharge la version distante.');
  const result = await api(db.settings, '/contents/data/state.enc.json?ref=monitor-data', {}, true);
  if (!result && (Object.keys(db.cloud.products || {}).length || db.cloud.alerts?.length)) throw new Error('L’historique GitHub a disparu. Le dernier relevé local est conservé.');
  const cloud = result ? normalizeCloud(await unseal(decodeContent(result.content), db.settings.key)) : EMPTY_CLOUD();
  try {
    const runData = await api(db.settings, '/actions/workflows/scan.yml/runs?per_page=1', {}, true);
    cloud.latestRun = runData?.workflow_runs?.[0] ? {at: runData.workflow_runs[0].created_at, status: runData.workflow_runs[0].status, conclusion: runData.workflow_runs[0].conclusion, url: runData.workflow_runs[0].html_url} : null;
  } catch (e) { cloud.workflowError = e.message; }
  const updates = {cloud, syncedAt: new Date().toISOString()};
  if (!db.dirty || replaceFavorites) Object.assign(updates, {favorites: remote.value.favorites, configSha: remote.sha, ...(replaceFavorites ? {dirty: false} : {})});
  await chrome.storage.local.set(updates);
  return read();
}
async function publish() {
  const db = await read(), remote = await remoteConfig(db.settings);
  if (remote.sha !== (db.configSha || null)) throw new Error('La liste distante a changé. Recharge-la avant de publier.');
  if (db.favorites.length > MAX_FAVORITES) throw new Error('La limite est de 50 favoris.');
  const encrypted = await seal({schema: 1, updatedAt: new Date().toISOString(), favorites: db.favorites}, db.settings.key);
  const response = await api(db.settings, '/contents/data/watchlist.enc.json', {method: 'PUT', body: JSON.stringify({
    message: 'favorites: encrypted update', content: encodeContent(encrypted), branch: db.settings.branch, ...(remote.sha ? {sha: remote.sha} : {})
  })});
  await chrome.storage.local.set({configSha: response.content.sha, dirty: false});
  return read();
}
async function addActive(tabId) {
  // Only a user-requested read of the open product page; no local monitoring.
  const results = await chrome.scripting.executeScript({target: {tabId: Number(tabId)}, world: 'MAIN', func: () => {
    const match = location.pathname.match(/^\/fr\/fr\/products\/(E\d{6}-\d{3})\/(\d{2})\/?$/);
    if (location.origin !== 'https://www.uniqlo.com' || !match) return null;
    const id = `${match[1]}-${match[2]}`;
    const product = window.__PRELOADED_STATE__?.entity?.pdpEntity?.[id]?.product;
    const selection = window.__PRELOADED_STATE__?.selection?.[match[1]];
    const color = selection?.colorDisplayCode || product?.representative?.color?.displayCode;
    return {id, url: location.origin + location.pathname, name: product?.name || document.querySelector('h1')?.textContent?.trim() || 'Article UNIQLO',
      image: product?.images?.main?.[color]?.image || null, color: product?.colors?.find(c => c.displayCode === color)?.name || '',
      size: product?.sizes?.find(s => s.displayCode === selection?.sizeDisplayCode)?.name || ''};
  }});
  if (!results?.[0]?.result) throw new Error('Ouvre une fiche produit UNIQLO France, puis clique sur l’extension.');
  return add(results[0].result);
}
async function add(favorite) {
  const db = await read(), parsed = canonical(favorite.url);
  if (db.favorites.some(f => f.id === parsed.id)) throw new Error('Cet article est déjà dans tes favoris.');
  if (db.favorites.length >= MAX_FAVORITES) throw new Error('La limite est de 50 favoris.');
  db.favorites.unshift({...parsed, name: String(favorite.name || 'Article UNIQLO').slice(0, 200), image: safeImage(favorite.image), color: String(favorite.color || '').slice(0, 80), size: String(favorite.size || '').slice(0, 40), enabled: true, targetCents: null, addedAt: new Date().toISOString()});
  await chrome.storage.local.set({favorites: db.favorites, dirty: true});
  return read();
}
async function handle(message) {
  await bootstrap();
  const db = await read();
  switch (message.type) {
    case 'read': return db;
    case 'addUrl': return add(message.favorite);
    case 'addActive': return addActive(message.tabId);
    case 'update': {
      const f = db.favorites.find(f => f.id === message.id);
      if (!f) throw new Error('Favori introuvable.');
      const patch = message.patch || {};
      if ('enabled' in patch) f.enabled = Boolean(patch.enabled);
      if ('targetCents' in patch) {
        if (patch.targetCents !== null && (!Number.isSafeInteger(patch.targetCents) || patch.targetCents <= 0 || patch.targetCents >= 10_000_000)) throw new Error('Objectif de prix invalide.');
        f.targetCents = patch.targetCents;
      }
      for (const k of ['color', 'size']) if (k in patch) f[k] = String(patch[k]).slice(0, k === 'size' ? 40 : 80);
      await chrome.storage.local.set({favorites: db.favorites, dirty: true}); return read();
    }
    case 'remove': await chrome.storage.local.set({favorites: db.favorites.filter(f => f.id !== message.id), dirty: true}); return read();
    case 'settings': {
      const input = message.settings || {};
      const s = {...db.settings};
      for (const name of ['repo', 'branch', 'token', 'key']) if (name in input) s[name] = String(input[name]).trim();
      repoPath(s);
      if (!validBranch(s.branch)) throw new Error('Nom de branche GitHub invalide.');
      s.token = s.token.trim(); s.key = s.key.trim();
      if (!s.key) throw new Error('Conservez la clé de chiffrement. Une clé vide rendrait la synchronisation impossible.');
      await seal({}, s.key);
      const changed = s.repo !== db.settings.repo || s.branch !== db.settings.branch || s.key !== db.settings.key;
      if (changed && db.favorites.length) throw new Error('Exporte tes favoris avant de changer de dépôt ou de clé. Ces champs se configurent avant l’ajout des articles.');
      await chrome.storage.local.set({settings: s, ...(changed ? {configSha: null, syncedAt: null, cloud: EMPTY_CLOUD()} : {})}); return read();
    }
    case 'sync': return sync();
    case 'publish': return publish();
    case 'reloadRemote': return sync({replaceFavorites: true});
    case 'scan': await api(db.settings, '/actions/workflows/scan.yml/dispatches', {method: 'POST', body: JSON.stringify({ref: db.settings.branch})}); return {requested: true};
    default: throw new Error('Commande inconnue.');
  }
}
// Serialize all mutations, including remote writes, to protect local revisions.
let queue = Promise.resolve();
chrome.runtime.onMessage.addListener((message, sender, reply) => {
  if (sender.id !== chrome.runtime.id) return false;
  const task = queue.then(() => handle(message));
  queue = task.catch(() => {});
  task.then(value => reply({ok: true, value}), error => reply({ok: false, error: error.message || 'Opération impossible.'}));
  return true;
});
