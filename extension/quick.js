/* Runs in an isolated content-script world, and in the toolbar popup. No site scripts or remote code. */
(() => {
  const embedded = location.protocol !== 'chrome-extension:';
  if (embedded && (location.origin !== 'https://www.uniqlo.com' || window.top !== window)) return;
  const host = document.createElement('div');
  if (embedded) host.style.cssText = 'all:initial!important;position:fixed!important;bottom:20px!important;right:20px!important;z-index:2147483647!important;width:min(360px,calc(100vw - 24px))!important;display:block!important;';
  document.body.append(host);
  const root = host.attachShadow({mode: 'closed'});
  // Constructable stylesheets work under the extension's strict style-src policy.
  const sheet = new CSSStyleSheet();
  sheet.replaceSync(`
      :host{color-scheme:light}*{box-sizing:border-box}button{font:inherit;cursor:pointer}button:focus-visible{outline:3px solid #2670bf;outline-offset:3px}button:disabled{cursor:wait;opacity:.6}
      .panel{font:14px/1.5 system-ui,sans-serif;color:#252525;background:#fff;border:1px solid #e6e1df;border-radius:18px;box-shadow:0 8px 40px #0002;overflow:hidden;text-align:left}
      header{display:flex;align-items:center;gap:10px;padding:16px 18px;border-bottom:1px solid #f0edeb}.mark{background:#e14343;color:white;border-radius:9px;font-size:20px;font-weight:800;padding:3px 9px}.brand{flex:1;font-weight:750}.brand small{display:block;font-size:11px;color:#777;font-weight:400}.close{border:0;background:transparent;font-size:23px;color:#777}
      .body{padding:16px 18px}h2{font-size:16px;line-height:1.4;margin:0 0 5px;overflow-wrap:anywhere}.muted{color:#76706d;font-size:12px;margin:0 0 12px}.primary{display:block;width:100%;background:#df4646;color:#fff;border:0;border-radius:10px;padding:12px;font-weight:650}.saved{background:#f5efed;color:#9c3030}
      .stats{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:16px 0}.stats button{background:#faf8f6;border:0;border-radius:10px;padding:9px 2px;color:#555;font-size:11px}.stats b{display:block;font-size:21px;color:#252525}.stats button:hover,.secondary:hover{background:#f0eae6}
      ul{margin:0 0 12px;padding:0;list-style:none}li{display:flex;gap:10px;justify-content:space-between;padding:6px 0;font-size:12px;border-bottom:1px solid #f2efed}li span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}li b{white-space:nowrap}
      .notice{font-size:12px;color:#776e68;background:#faf7f1;padding:9px;border-radius:8px;margin:0 0 10px}.message{font-size:12px;color:#526e4b;margin:8px 0;overflow-wrap:anywhere}.error{color:#b32c2c}.secondary{width:100%;padding:10px;border:1px solid #e6e1df;background:white;border-radius:9px;font-weight:600;color:#333}.links{display:flex;gap:12px;margin-top:10px}.links button{padding:0;background:none;border:0;font-size:12px;color:#76706d;text-decoration:underline}.launcher{font:600 14px system-ui,sans-serif;border:0;border-radius:30px;background:#df4646;color:white;padding:13px 18px;box-shadow:0 5px 22px #0003;float:right}[hidden]{display:none!important}
      @media(max-height:600px){.panel.floating{max-height:85vh;overflow:auto}}

  `);
  root.adoptedStyleSheets = [sheet];
  root.innerHTML = `

    <section class="panel" aria-label="UNIQLO Alert"><header><span class="mark" aria-hidden="true">U↓</span><div class="brand">UNIQLO Alert<small>Vos envies, au bon prix</small></div><button class="close" aria-label="Réduire la fenêtre" title="Réduire">−</button></header>
    <div class="body"><h2>Vos favoris à portée de clic</h2><p class="muted" id="productInfo">Chargement…</p><button class="primary" id="toggle" disabled>Chargement…</button>
    <div class="stats"><button data-view="favorites"><b id="count">0</b>Favoris</button><button data-view="favorites" data-filter="drop"><b id="drops">0</b>En baisse</button><button data-view="alerts"><b id="alerts">0</b>Alertes</button></div>
    <ul aria-label="Derniers favoris"></ul><p class="notice" id="notice"></p><p class="message" role="status" aria-live="polite"></p>
    <button class="secondary" id="dashboard">Ouvrir mes favoris ↗</button><div class="links"><button id="refresh">Actualiser l’aperçu</button><button data-view="settings">Réglages</button></div></div></section>
    <button class="launcher" aria-label="Ouvrir UNIQLO Alert" hidden>♡ UNIQLO Alert</button>`;
  const $ = selector => root.querySelector(selector);
  if (embedded) $('.panel').classList.add('floating');
  let url = embedded ? location.href : '', pageName = '', pending = false, sequence = 0, stopped = false;
  const money = value => Number.isSafeInteger(value) ? new Intl.NumberFormat('fr-FR', {style:'currency',currency:'EUR'}).format(value / 100) : '—';
  const message = (text, error = false) => { $('.message').textContent = text; $('.message').classList.toggle('error', error); };
  const call = async (type, values = {}) => {
    const response = await chrome.runtime.sendMessage({type, url, ...values});
    if (!response?.ok) throw new Error(response?.error || 'Extension indisponible. Rechargez cette page.');
    return response.value;
  };
  const title = () => embedded ? document.querySelector('h1')?.textContent?.trim() || 'Article UNIQLO' : pageName.replace(/\s*[|｜].*$/, '') || 'Article UNIQLO';
  function render(summary) {
    const p = summary.product;
    $('h2').textContent = p ? p.name || title() : 'Vos favoris à portée de clic';
    $('#productInfo').textContent = p ? `${p.id} · ${p.lastSuccessfulAt ? `Dernier prix relevé : ${money(p.priceCents)}` : 'Prix en attente du premier relevé'}` : 'Ouvrez une fiche UNIQLO France pour ajouter l’article.';
    $('#toggle').hidden = !p;
    $('#toggle').textContent = p?.saved ? '♥ Retirer de mes favoris' : '♡ Ajouter à mes favoris';
    $('#toggle').classList.toggle('saved', !!p?.saved);
    $('#toggle').disabled = pending || !p;
    for (const key of ['count', 'drops', 'alerts']) $('#' + key).textContent = summary[key];
    $('ul').replaceChildren(...summary.preview.map(item => {
      const row = document.createElement('li'), name = document.createElement('span'), price = document.createElement('b');
      name.textContent = item.name; price.textContent = money(item.priceCents); row.append(name, price); return row;
    }));
    $('#notice').textContent = summary.dirty ? 'Modifications enregistrées sur cet appareil. Publiez-les dans le tableau de bord pour mettre à jour les scans GitHub.' : summary.connected ? 'Aperçu des derniers relevés reçus. Les prix ne sont pas actualisés en temps réel.' : 'Les favoris fonctionnent sans connexion. Configurez GitHub pour recevoir les relevés de prix.';
    $('#dashboard').textContent = summary.dirty ? 'Ouvrir et publier mes favoris ↗' : 'Ouvrir mes favoris ↗';
  }
  async function refresh() {
    if (stopped || pending) return;
    const version = ++sequence;
    try {
      if (!embedded) {
        const [tab] = await chrome.tabs.query({active:true,currentWindow:true});
        url = tab?.url || ''; pageName = tab?.title || '';
      }
      const summary = await call('quickRead');
      if (version === sequence && !pending) render(summary);
    } catch (error) { message(error.message, true); }
  }
  $('#toggle').onclick = async () => {
    if (pending) return;
    pending = true; ++sequence; $('#toggle').disabled = true;
    try {
      const summary = await call('quickToggle', {name:title()});
      message(summary.product.saved ? 'Article ajouté à vos favoris.' : 'Article retiré de vos favoris.');
      pending = false; render(summary);
    } catch (error) { message(error.message, true); }
    finally { pending = false; await refresh(); }
  };
  const open = async (view, filter) => { try { await call('openDashboard', {view, filter}); if (!embedded) window.close(); } catch (error) { message(error.message, true); } };
  $('#dashboard').onclick = () => open('favorites');
  root.querySelectorAll('[data-view]').forEach(button => button.onclick = () => open(button.dataset.view, button.dataset.filter));
  $('#refresh').onclick = () => { message(''); refresh(); };
  $('.close').hidden = !embedded;
  $('.close').onclick = () => { $('.panel').hidden = true; $('.launcher').hidden = false; $('.launcher').focus(); };
  $('.launcher').onclick = () => { $('.panel').hidden = false; $('.launcher').hidden = true; $('.close').focus(); refresh(); };
  window.addEventListener('focus', refresh);
  // Only local state and URL changes; never fetch or scan UNIQLO automatically.
  if (embedded) {
    let ticks = 0;
    const interval = setInterval(() => {
      if (!chrome.runtime?.id) { stopped = true; clearInterval(interval); return; }
      if (url !== location.href) { url = location.href; message(''); refresh(); }
      else if (++ticks % 10 === 0 && !document.hidden && !$('.panel').hidden) refresh();
    }, 1000);
  }
  refresh();
})();
