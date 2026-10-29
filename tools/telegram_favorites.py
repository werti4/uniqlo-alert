"""Private, read-only list of published favorites with the last known prices."""
import base64
import datetime as dt
import json
from urllib.parse import quote
from zoneinfo import ZoneInfo

from scanner.monitor import decrypt, validate_favorites, validate_state


def valid_price(value):
    return type(value) is int and 0 < value < 10_000_000


def money(value):
    return f'{value // 100},{value % 100:02d} €'


def render(favorites, state, *, now=None, state_ok=True):
    if not favorites:
        return ['Vous n’avez aucun favori publié sur GitHub. Ajoutez vos articles dans l’extension, puis publiez vos favoris.']
    now = now or dt.datetime.now(dt.timezone.utc)
    header = (f'♡ Vos favoris publiés : {len(favorites)}\n'
              '🔴 Promotion au dernier relevé · ⚪ Pas de promotion confirmée · ⚫ Prix indisponible\n'
              'Lecture seule : aucun scan lancé. Prix connus, pas des prix en temps réel.\n')
    if not state_ok:
        header += '⚠️ Relevés non accessibles : la liste est disponible, mais aucun prix ne peut être confirmé.\n'
    products = state.get('products', {}) if state_ok else {}
    chunks, chunk = [], header
    for index, favorite in enumerate(favorites, 1):
        p = products.get(favorite['id'], {})
        price, base = p.get('priceCents'), p.get('regularCents')
        known = valid_price(price)
        promo = known and valid_price(base) and price < base
        marker = '🔴' if promo else '⚪' if known else '⚫'
        name = str(favorite.get('name') or p.get('name') or 'Article UNIQLO').replace('\n', ' ')[:200]
        lines = [f'{marker} {index}. {name}' + (' · En pause' if not favorite.get('enabled', True) else '')]
        if promo:
            lines.append(f'{money(price)} au lieu de {money(base)} (−{round((base-price)*100/base)} %)')
        elif known:
            lines.append(money(price))
            if not valid_price(base):
                lines.append('Prix de base indisponible : promotion non vérifiable.')
        else:
            lines.append('Prix indisponible : aucun relevé valide reçu.')
        if known:
            try:
                stamp = dt.datetime.fromisoformat(p.get('lastSuccessfulAt') or p.get('lastCheckedAt'))
                if stamp.tzinfo is None:
                    raise ValueError()
                label = stamp.astimezone(ZoneInfo('Europe/Paris')).strftime('%d/%m %H:%M')
                lines.append('Relevé : ' + label + (' · ancien, à vérifier' if (now-stamp).total_seconds() > 2700 else ''))
            except (TypeError, ValueError):
                lines.append('Date du relevé indisponible : prix à vérifier.')
        if p.get('status') == 'error':
            lines.append('⚠️ Dernière lecture en erreur ; dernier prix valide conservé.')
        lines.append(favorite['url'])
        block = '\n'.join(lines)
        if len(chunk) + len(block) + 2 > 3500:
            chunks.append(chunk); chunk = '♡ Vos favoris — suite\n'
        chunk += '\n' + block + '\n'
    chunks.append(chunk)
    return chunks


def messages(github, key, branch='main'):
    try:
        record = github.api('/contents/data/watchlist.enc.json?ref=' + quote(branch, safe=''))
        if not record:
            return ['Liste publiée introuvable. Publiez vos favoris depuis l’extension ; aucune liste locale n’a été modifiée.']
        config = decrypt(json.loads(base64.b64decode(record['content'])), key)
        favorites = validate_favorites(config)
    except Exception:
        return ['Impossible de lire la liste chiffrée des favoris. Vérifiez la connexion GitHub et la clé ; aucune donnée n’a été remplacée.']
    try:
        state = validate_state(github.load(key))
        return render(favorites, state)
    except Exception:
        return render(favorites, {}, state_ok=False)
