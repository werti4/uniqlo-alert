"""Execute one explicitly requested private /scan, preserving scanner safeguards."""
import json
import os
from pathlib import Path

from scanner import monitor


def money(value):
    return f'{value // 100},{value % 100:02d} €'


def results(state, favorites, at):
    active = [f for f in favorites if f.get('enabled', True)]
    if not active:
        return ['Aucun favori actif publié à scanner. Ajoutez puis publiez vos favoris dans l’extension.']
    products = state.get('products', {})
    checked, unknown, promos = 0, 0, []
    for favorite in active:
        product = products.get(favorite['id'], {})
        # Only include prices successfully obtained during THIS scan, never old prices.
        if product.get('status') != 'ok' or product.get('lastSuccessfulAt') != at:
            continue
        checked += 1
        price, base = product.get('priceCents'), product.get('regularCents')
        if type(price) is not int or type(base) is not int or not 0 < price <= base:
            unknown += 1
            continue
        if price < base:
            name = str(product.get('name') or favorite.get('name') or 'Article UNIQLO').replace('\n', ' ')[:200]
            promos.append(f"• {name}\n{money(price)} au lieu de {money(base)} (−{round((base-price)*100/base)} %)\n{favorite['url']}")
    messages = [f'Articles vérifiés : {checked}/{len(active)}.']
    if promos:
        messages.append(f'🏷️ {len(promos)} article(s) actuellement en promotion parmi les articles vérifiés. Les promotions déjà présentes avant l’ajout sont incluses.')
        chunk = ''
        for item in promos:
            if len(chunk) + len(item) + 2 > 3500:
                messages.append(chunk); chunk = ''
            chunk += ('\n\n' if chunk else '') + item
        if chunk:
            messages.append(chunk)
    elif checked == len(active) and not unknown:
        messages.append('Aucun article en promo parmi vos favoris actifs publiés.')
    else:
        messages.append('Aucune promotion confirmée sur les articles vérifiés. Impossible de conclure pour les articles en erreur ou différés.')
    if checked < len(active) or unknown:
        messages.append('⚠️ Vérification incomplète : articles en erreur, différés, pause UNIQLO ou comparaison au prix de base indisponible. Les derniers prix valides sont conservés ; utilisez /logs pour le diagnostic.')
    messages.append('Prix du groupe produit ; stock et prix par taille/couleur non vérifiés.')
    return messages


def execute(send):
    try:
        key = os.environ['UA_ENCRYPTION_KEY']
        favorites = monitor.validate_favorites(monitor.decrypt(json.loads(Path('data/watchlist.enc.json').read_text()), key))
        storage = monitor.GitHubState(os.environ['GITHUB_TOKEN'], os.environ['GITHUB_REPOSITORY'])
        state = monitor.validate_state(storage.load(key))
        at = monitor.now()
        state.update(lastScanAt=at, telegramConfigured=True,
                     runUrl=f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}")
        active_ids = {f['id'] for f in favorites}
        state['products'] = {k:v for k,v in state['products'].items() if k in active_ids}
        state['alerts'] = [e for e in state['alerts'] if e['productId'] in active_ids]
        monitor.scan_products(state, favorites, at)  # Includes robots.txt, backoff and bounded requests.
        state['persistedAt'] = at
        storage.save(state, key)  # Also persist unchanged successful prices and the outbox before delivery.
        if any(e['delivery'] == 'pending' for e in state['alerts']):
            monitor.deliver_outbox(state, storage, key, monitor.now())
        messages = results(state, favorites, at)
        incomplete = bool(state.get('scanError'))
    except Exception:
        send('⚠️ Scan terminé avec une erreur. Impossible de confirmer les promotions. Consultez /logs et l’exécution Actions ; aucun prix fictif n’a été enregistré.')
        return
    send('⚠️ Scan terminé avec des articles non vérifiés.' if incomplete else '✅ Scan terminé.')
    for message in messages:
        send(message)
