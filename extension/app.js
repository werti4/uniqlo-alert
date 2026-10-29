import {money, relative, canonical, safeImage} from './core.js';

const $ = selector => document.querySelector(selector);
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let db, filter = 'all', search = '', sort = 'recent', busy = false, timer, settingsDraftDirty = false;
const demo = !globalThis.chrome?.runtime?.id;
let call = async (type, values = {}) => {
  const r = await chrome.runtime.sendMessage({type, ...values});
  if (!r.ok) throw new Error(r.error);
  return r.value;
};
function toast(text, error = false) {
  $('#toast').textContent = text; $('#toast').className = 'visible' + (error ? ' error' : '');
  clearTimeout(timer); timer = setTimeout(() => $('#toast').className = '', 6500);
}
async function perform(action, success, redraw = true) {
  if (busy) return;
  busy = true;
  document.body.setAttribute('aria-busy', 'true');
  document.querySelectorAll('button:not([data-close]):not([data-view]):not([data-filter])').forEach(b => b.disabled = true);
  try {
    const value = await action();
    if (redraw) { db = value; render(); }
    if (success) toast(success);
    return value;
  } catch (e) { toast(e.message, true); }
  finally {
    busy = false; document.body.removeAttribute('aria-busy');
    document.querySelectorAll('button').forEach(b => b.disabled = false);
  }
}
function view(name) {
  for (const panel of document.querySelectorAll('.view')) panel.hidden = panel.id !== name + 'View';
  for (const nav of document.querySelectorAll('[data-view]')) nav.classList.toggle('active', nav.dataset.view === name);
  $('#breadcrumb').innerHTML = `MON ESPACE <span>/</span> ${{favorites:'MES FAVORIS',alerts:'MES ALERTES',settings:'RÉGLAGES'}[name]}`;
}
function dropFor(p) { return p.firstPriceCents && p.priceCents ? Math.max(0, p.firstPriceCents - p.priceCents) : 0; }
function render() {
  const list = db.favorites.map(f => ({...f, ...db.cloud.products?.[f.id], favorite: f}));
  $('#navCount').textContent = db.favorites.length;
  $('#allCount').textContent = db.favorites.length;
  $('#alertCount').textContent = db.cloud.alerts?.length || 0;
  $('#statFollowed').innerHTML = `${list.filter(p => p.favorite.enabled).length}<small>favoris actifs</small>`;
  $('#statDrops').innerHTML = `${list.filter(p => dropFor(p) > 0).length}<small>par rapport au premier prix relevé</small>`;
  const latest = db.cloud.latestRun;
  const validDates = Object.values(db.cloud.products || {}).map(p => p.lastSuccessfulAt || p.lastCheckedAt).filter(at => at && Number.isFinite(Date.parse(at))).sort();
  const lastSuccess = validDates.at(-1);
  const stats = db.cloud.scanStats;
  const stale = !!lastSuccess && Date.now() - Date.parse(lastSuccess) > 45 * 60_000;
  const cooling = Date.parse(db.cloud.cooldownUntil) > Date.now();
  const running = ['in_progress', 'queued', 'waiting', 'requested'].includes(latest?.status);
  const scanHint = cooling ? 'Surveillance temporairement suspendue' : running ? 'Nouvelle exécution GitHub en attente ou en cours' : stale ? 'Relevé ancien · consulter les exécutions' : stats?.deferred ? `${stats.succeeded || 0} réussis · ${stats.deferred} différés` : 'Planifié toutes les 5 min · retards possibles';
  $('#statScan').innerHTML = `${escape(relative(lastSuccess))}<small>${escape(scanHint)}</small>`;
  const configured = !!db.settings.token && !!db.settings.key;
  const connected = configured && !!db.syncedAt;
  $('#cloudDot').className = connected ? 'ok' : configured ? 'warning' : '';
  $('#cloudLabel').textContent = connected ? 'GitHub synchronisé' : configured ? 'Connexion à vérifier' : 'À configurer';
  const issue = db.cloud.scanError || (db.cloud.telegramConfigured ? db.cloud.notificationError : '') || db.cloud.workflowError ||
    (cooling ? `Prochaine tentative après ${new Date(db.cloud.cooldownUntil).toLocaleString('fr-FR')}.` : '') ||
    (latest?.conclusion === 'failure' ? 'La dernière exécution GitHub a échoué.' : '') ||
    (stale ? 'Les derniers prix reçus datent de plus de 45 minutes.' : '');
  $('#connectionBanner').hidden = connected && !issue && !!lastSuccess;
  if (!$('#connectionBanner').hidden) {
    $('#connectionBanner b').textContent = issue || (connected ? lastSuccess ? 'Les notifications Telegram restent à configurer.' : 'Aucun relevé réussi reçu pour le moment.' : configured ? 'Connexion enregistrée. Actualisez pour la vérifier.' : 'Votre veille commence ici.');
    $('#connectionBanner p').textContent = configured ? 'Consultez les réglages et les dernières exécutions GitHub. Une exécution réussie ne garantit pas un relevé de prix.' : 'Connectez le dépôt GitHub, puis ajoutez votre premier article.';
  }
  $('#syncDot').className = db.dirty ? 'warning' : connected ? 'ok' : '';
  $('#syncText').textContent = db.dirty ? 'Modifications locales à publier sur GitHub' : db.syncedAt ? 'Données GitHub · ' + relative(db.syncedAt).toLowerCase() : 'Favoris enregistrés sur cet appareil';
  let shown = list.filter(p => (filter !== 'drop' || dropFor(p) > 0) && (filter !== 'paused' || !p.favorite.enabled) && (!search || `${p.name} ${p.id} ${p.favorite.color}`.toLowerCase().includes(search)));
  if (sort === 'price') shown.sort((a,b) => (a.priceCents ?? Infinity) - (b.priceCents ?? Infinity));
  if (sort === 'drop') shown.sort((a,b) => dropFor(b) - dropFor(a));
  if (sort === 'recent') shown.sort((a,b) => (Date.parse(b.favorite.addedAt) || 0) - (Date.parse(a.favorite.addedAt) || 0));
  $('#grid').innerHTML = shown.map(card).join('');
  $('#empty').hidden = shown.length > 0;
  if (!shown.length && db.favorites.length) {
    $('#empty h2').textContent = 'Aucun article dans cette sélection.';
    $('#empty p').textContent = 'Essayez un autre filtre ou un autre mot-clé.';
    $('#emptyAdd').hidden = true;
  } else {
    $('#empty h2').textContent = 'Votre prochaine bonne affaire commence ici.';
    $('#empty p').textContent = 'Ouvrez une fiche UNIQLO et cliquez sur l’extension, ou ajoutez simplement son lien.';
    $('#emptyAdd').hidden = false;
  }
  $('#alertsList').innerHTML = (db.cloud.alerts || []).slice().sort((a,b) => b.at.localeCompare(a.at)).map(e => `<article class="alert-row"><span class="alert-symbol">↘</span><div class="alert-text"><b>${escape(e.name)}</b><p>${escape(new Date(e.at).toLocaleString('fr-FR'))} · <span class="delivery">${e.delivery === 'sent' ? 'Envoyée sur Telegram' : 'En attente d’envoi'}</span></p></div><div class="alert-price"><del>${money(e.oldCents)}</del>${money(e.newCents)}</div><a href="${escape(canonical(e.url).url)}" class="button" target="_blank" rel="noreferrer">Voir l’article ↗</a></article>`).join('') || '<div class="empty"><div class="empty-heart">↘</div><h2>Les prochaines baisses apparaîtront ici.</h2><p>Le premier relevé sert de référence. Il ne déclenche pas d’alerte.</p></div>';
  if (!settingsDraftDirty) {
    $('#repo').value = db.settings.repo;
    $('#branch').value = db.settings.branch;
    $('#token').value = db.settings.token;
    $('#key').value = db.settings.key;
  }
  const validRepo = /^[\w.-]+\/[\w.-]+$/.test(db.settings.repo) ? db.settings.repo : 'werti4/uniqlo-alert';
  $('#secretsLink').href = `https://github.com/${validRepo}/settings/secrets/actions`;
  $('#actionsLink').href = `https://github.com/${validRepo}/actions`;
  $('#scanHealth').textContent = `Dernière tentative : ${db.cloud.lastScanAt ? new Date(db.cloud.lastScanAt).toLocaleString('fr-FR') : 'aucune reçue'}${stats ? ` · ${stats.succeeded || 0} réussis, ${stats.failed || 0} en erreur, ${stats.deferred || 0} différés` : ''}${latest ? ` · GitHub : ${running ? 'en cours ou en attente' : latest.conclusion === 'success' ? 'dernière exécution terminée' : latest.conclusion || latest.status}` : ''}.`;
  for (const img of $('#grid').querySelectorAll('img')) img.addEventListener('error', () => {
    const fallback = document.createElement('div'); fallback.className = 'placeholder'; fallback.textContent = 'U'; img.replaceWith(fallback);
  }, {once: true});
}
function card(p) {
  const f = p.favorite;
  const sale = Number.isSafeInteger(p.priceCents) && p.regularCents > p.priceCents;
  const image = safeImage(p.image || f.image);
  const targetReached = f.targetCents && Number.isSafeInteger(p.priceCents) && p.priceCents <= f.targetCents;
  return `<article class="product-card"><div class="product-photo">${image ? `<img src="${escape(image)}" alt="${escape(p.name)}" loading="lazy">` : '<div class="placeholder">U</div>'}${!f.enabled ? '<span class="product-tag paused">En pause</span>' : sale ? '<span class="product-tag sale">Promotion affichée</span>' : '<span class="product-tag">Favori</span>'}<button class="favorite-icon" data-detail="${escape(p.id)}" title="Gérer ce favori" aria-label="Gérer ${escape(p.name)}">♥</button></div><div class="product-info"><div class="product-id">UNIQLO · ${escape(p.id.replace('E',''))}</div><h3>${escape(p.name)}</h3><div class="product-meta">${escape([f.color, f.size ? 'Taille souhaitée : ' + f.size : ''].filter(Boolean).join(' · ') || 'Préférences à renseigner')}</div><div class="price-row"><span class="price ${sale ? 'sale' : ''}">${money(p.priceCents)}</span>${sale ? `<del>${money(p.regularCents)}</del><span class="saving">−${Math.round((p.regularCents-p.priceCents)*100/p.regularCents)} %</span>` : ''}</div>${targetReached ? '<div class="target-reached">✓ Objectif de prix atteint</div>' : ''}<div class="card-bottom"><span class="status ${p.status === 'error' ? 'error' : ''}"><i></i>${!f.enabled ? 'Surveillance en pause' : p.status === 'error' ? 'Lecture à vérifier' : p.lastCheckedAt ? escape(relative(p.lastCheckedAt)) : 'Premier scan en attente'}</span><button data-detail="${escape(p.id)}">Détails ↗</button></div><div class="stock-hint">Stock et couleur à vérifier sur UNIQLO</div></div></article>`;
}
function detail(id) {
  const f = db.favorites.find(f => f.id === id), p = db.cloud.products?.[id] || {};
  if (!f) return;
  $('#detailTitle').textContent = p.name || f.name;
  const history = p.history || [];
  let chart = '';
  if (history.length > 1) {
    const vals = history.map(h => h.priceCents), lo = Math.min(...vals), hi = Math.max(...vals);
    const points = vals.map((v,i) => `${10+i*380/(vals.length-1)},${85-(v-lo)*65/Math.max(100,hi-lo)}`).join(' ');
    chart = `<svg class="history-chart" viewBox="0 0 400 100" role="img" aria-label="Historique des changements de prix"><polyline points="${points}" fill="none" stroke="#dd4c4b" stroke-width="2.5"/></svg>`;
  }
  $('#detailBody').innerHTML = `${p.status === 'error' ? `<p class="error-notice">${escape(p.error)}. Le dernier prix valide est conservé.</p>` : ''}<div class="detail-prices"><div>DERNIER PRIX<strong>${money(p.priceCents)}</strong></div><div>PLUS BAS OBSERVÉ<strong>${money(p.lowestCents)}</strong></div></div><p class="detail-status">${escape(relative(p.lastCheckedAt))} · ${escape(p.stockNote || 'Stock par taille non vérifié')}</p>${p.sizes?.length ? `<p class="detail-status">Tailles au catalogue : ${escape(p.sizes.join(' · '))}</p>` : ''}${p.rating ? `<p class="detail-status">Avis : ${escape(p.rating)} / 5 (${escape(p.reviewCount || 0)})</p>` : ''}${chart}<table class="history-table"><tbody>${history.slice(-5).reverse().map(h => `<tr><td>${escape(new Date(h.at).toLocaleString('fr-FR'))}</td><td>${money(h.priceCents)}</td></tr>`).join('') || '<tr><td>Aucun relevé disponible</td><td>—</td></tr>'}</tbody></table><form id="detailForm" class="detail-form"><label>Couleur souhaitée<input id="detailColor" value="${escape(f.color)}" maxlength="80"></label><label>Taille souhaitée<input id="detailSize" value="${escape(f.size)}" maxlength="40"></label><label>Objectif de prix en euros (facultatif)<input id="detailTarget" type="number" min="0.01" step="0.01" placeholder="Exemple : 19,90" value="${f.targetCents ? f.targetCents/100 : ''}"></label><p class="field-help target-help">Toutes les baisses restent signalées, même au-dessus de cet objectif. Couleur et taille sont des souhaits ; leur disponibilité et leur prix ne sont pas vérifiés séparément.</p><button class="button primary">Enregistrer les préférences</button></form><div class="detail-links"><a class="button" href="${escape(canonical(f.url).url)}" target="_blank" rel="noreferrer">Voir sur UNIQLO ↗</a><button class="button" id="toggleFavorite">${f.enabled ? 'Mettre en pause' : 'Reprendre le suivi'}</button><button class="button danger" id="deleteFavorite">Retirer</button></div>`;
  $('#detailForm').onsubmit = event => {
    event.preventDefault();
    const raw = $('#detailTarget').value;
    perform(() => call('update', {id, patch: {color: $('#detailColor').value, size: $('#detailSize').value, targetCents: raw ? Math.round(Number(raw)*100) : null}}), 'Préférences enregistrées. Pensez à les publier.').then(value => { if (value) $('#detailDialog').close(); });
  };
  $('#toggleFavorite').onclick = () => perform(() => call('update', {id, patch: {enabled: !f.enabled}}), 'Favori modifié. Pensez à publier.').then(value => { if(value) $('#detailDialog').close(); });
  $('#deleteFavorite').onclick = () => { if (confirm('Retirer cet article des favoris ?')) perform(() => call('remove', {id}), 'Article retiré localement. Pensez à publier.').then(value => {if(value) $('#detailDialog').close();}); };
  $('#detailDialog').showModal();
}
function exportFavorites() {
  const blob = new Blob([JSON.stringify({schema:1,favorites:db.favorites}, null, 2)], {type:'application/json'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'mes-favoris-uniqlo.json'; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  toast('Export sans jeton ni clé. Les articles sont en clair dans ce fichier.');
}
function bind() {
  $('.brand').onclick = event => {event.preventDefault(); view('favorites');};
  $('#settingsForm').oninput = () => {settingsDraftDirty = true;};
  document.querySelectorAll('[data-view]').forEach(el => el.onclick = () => view(el.dataset.view));
  document.querySelectorAll('[data-filter]').forEach(el => el.onclick = () => { filter = el.dataset.filter; document.querySelectorAll('[data-filter]').forEach(b => b.classList.toggle('active', b === el)); render(); });
  document.querySelectorAll('[data-close]').forEach(el => el.onclick = () => $('#'+el.dataset.close).close());
  for (const selector of ['#addButton','#emptyAdd']) $(selector).onclick = () => $('#addDialog').showModal();
  $('#setupButton').onclick = () => view('settings');
  $('#search').oninput = event => {search = event.target.value.toLowerCase(); render();};
  $('#sort').onchange = event => {sort = event.target.value; render();};
  $('#grid').onclick = event => { const button = event.target.closest('[data-detail]'); if (button) detail(button.dataset.detail); };
  $('#refresh').onclick = () => perform(() => call('sync'), 'Données actualisées.');
  const publish = () => perform(() => call('publish'), 'Favoris chiffrés publiés sur GitHub.');
  $('#publish').onclick = publish; $('#publishSettings').onclick = publish;
  $('#settingsForm').onsubmit = event => {event.preventDefault(); perform(() => call('settings', {settings: {repo:$('#repo').value.trim(),branch:$('#branch').value.trim(),token:$('#token').value,key:$('#key').value}}).then(value => {settingsDraftDirty = false; return value;}), 'Connexion enregistrée. Actualisez pour la vérifier.');};
  $('#copyKey').onclick = async () => {try {await navigator.clipboard.writeText($('#key').value); toast('Clé copiée. À enregistrer uniquement dans UA_ENCRYPTION_KEY.');} catch {toast('Copiez la clé manuellement dans ce champ.', true);}};
  $('#scanNow').onclick = () => perform(() => call('scan'), 'Scan demandé. GitHub le placera dans sa file d’attente.', false);
  $('#exportFavorites').onclick = exportFavorites;
  $('#reloadRemote').onclick = () => {if(confirm('Remplacer les favoris locaux par la version GitHub ? Les changements non publiés seront perdus.')) perform(() => call('reloadRemote'), 'Liste distante chargée.');};
  $('#addForm').onsubmit = event => {event.preventDefault(); perform(() => call('addUrl', {favorite:{url:$('#productUrl').value,name:$('#productName').value}}), 'Favori ajouté. Publiez-le pour lancer sa surveillance.').then(value => {if(value) {$('#addDialog').close(); $('#addForm').reset();}});};
}
async function start() {
  if (demo) {
    const module = await import('./demo.js');
    db = module.demoData();
    call = module.demoCall;
    const banner = document.createElement('div'); banner.className = 'demo-banner'; banner.textContent = 'APERÇU DE DÉMONSTRATION · Prix et articles illustratifs · Aucun scan réel'; document.body.prepend(banner);
  } else db = await call('read');
  if (new URL(location.href).searchParams.get('filter') === 'drop') {
    filter = 'drop';
    document.querySelectorAll('[data-filter]').forEach(button => button.classList.toggle('active', button.dataset.filter === filter));
  }
  bind(); render();
  const requestedView = new URL(location.href).searchParams.get('view');
  if (['favorites', 'alerts', 'settings'].includes(requestedView)) view(requestedView);
  if (!db.settings.token && !requestedView) view('settings');
  if (db.settings.token && !demo) await perform(() => call('sync'), null);
  const source = new URL(location.href).searchParams.get('source');
  if (source && !demo) {
    await perform(() => call('addActive', {tabId:Number(source)}), 'Article ajouté depuis la fiche ouverte. Publiez-le pour activer son suivi.');
    const url = new URL(location.href); url.searchParams.delete('source'); history.replaceState(null, '', url);
  }
}
start().catch(e => toast(e.message, true));
