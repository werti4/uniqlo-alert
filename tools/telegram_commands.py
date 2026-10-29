"""Private /logs diagnostics. Never scan products or modify scanner snapshots."""
import base64
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from zoneinfo import ZoneInfo

from scanner.monitor import GitHubState, decrypt, encrypt

CURSOR_PATH = '/contents/data/telegram-commands.enc.json?ref=monitor-data'
MAX_REPLIES = 3


def telegram(token, method, payload):
    request = urllib.request.Request(
        f'https://api.telegram.org/bot{token}/{method}',
        data=json.dumps(payload).encode(), method='POST',
        headers={'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.load(response)
        if not isinstance(result, dict) or result.get('ok') is not True:
            raise ValueError()
        return result['result']
    except Exception:
        # Telegram errors can contain URLs with the bot token. Never propagate them.
        raise RuntimeError('Requête Telegram non confirmée ; réessayer ultérieurement.') from None


def date(value):
    try:
        stamp = dt.datetime.fromisoformat(value)
        if stamp.tzinfo is None:
            return 'non disponible'
        return stamp.astimezone(ZoneInfo('Europe/Paris')).strftime('%d/%m %H:%M:%S')
    except (ValueError, TypeError):
        return 'non disponible'


def number(value):
    return value if type(value) is int and 0 <= value <= 100000 else 0


def diagnostics(state, runs, repo, *, state_ok=True, runs_ok=True):
    stats = state.get('scanStats') or {}
    if not isinstance(stats, dict):
        stats = {}
    products = state.get('products') or {}
    products = products if isinstance(products, dict) else {}
    successful_dates = [p.get('lastSuccessfulAt') or p.get('lastCheckedAt') for p in products.values() if isinstance(p, dict)]
    valid_dates = [value for value in successful_dates if date(value) != 'non disponible']
    last_product = max(valid_dates, key=lambda value: dt.datetime.fromisoformat(value)) if valid_dates else None
    lines = [
        '📋 UNIQLO Alert — diagnostic /logs',
        'Heures de Paris. Lecture seule : aucun scan lancé.',
        '',
        f"Dernière tentative : {date(state.get('lastScanAt'))}",
        f'Dernière lecture valide reçue : {date(last_product)}',
        f"Dernier passage : {number(stats.get('succeeded'))} réussis · {number(stats.get('failed'))} erreurs · {number(stats.get('deferred'))} différés",
        'Collecte : ' + ('erreur ou suspension signalée' if state.get('scanError') else 'aucune erreur enregistrée' if state.get('lastScanAt') else 'non vérifiée'),
        'Pause jusqu’au : ' + date(state.get('cooldownUntil')),
        'Telegram : ' + ('erreur d’envoi enregistrée' if state.get('notificationError') else 'aucune erreur enregistrée'),
    ]
    if not state_ok:
        lines.append('⚠️ État chiffré non accessible : compteurs et dates indisponibles.')
    lines += ['', 'Dernières exécutions GitHub :']
    events = {'schedule': 'planifié', 'push': 'commit', 'workflow_dispatch': 'manuel'}
    statuses = {'success': 'réussi', 'failure': 'échec', 'cancelled': 'annulé', 'skipped': 'ignoré', 'timed_out': 'délai dépassé'}
    for run in runs[:5]:
        run_id = run.get('id')
        if type(run_id) is not int or run_id <= 0:
            continue
        status = statuses.get(run.get('conclusion'), 'en cours ou en attente' if run.get('status') != 'completed' else 'terminé')
        lines += [f"{date(run.get('created_at'))} · {events.get(run.get('event'), 'autre')} · {status}", f'https://github.com/{repo}/actions/runs/{run_id}']
    if not runs_ok:
        lines.append('⚠️ Historique Actions indisponible.')
    elif not runs:
        lines.append('Aucune exécution disponible.')
    elif not any(run.get('event') == 'schedule' for run in runs):
        lines.append('⚠️ Aucun lancement planifié parmi ces exécutions. Cadence automatique non confirmée.')
    lines += ['', 'Les dates viennent du dernier état sauvegardé ; elles peuvent être anciennes. Un workflow vert ne garantit pas une lecture par article.']
    return '\n'.join(lines)


class CommandStore:
    def __init__(self, github, key):
        self.github, self.key, self.sha = github, key, None

    def load(self):
        record = self.github.api(CURSOR_PATH)
        if record is None:
            return None
        self.sha = record['sha']
        data = decrypt(json.loads(base64.b64decode(record['content'])), self.key)
        cursor = data.get('lastUpdateId')
        if data.get('schema') != 1 or type(cursor) is not int or cursor < 0:
            raise ValueError('État de commandes incompatible ; aucune donnée remplacée.')
        return cursor

    def save(self, cursor):
        payload = {
            'branch': 'monitor-data', 'message': 'telegram: encrypted command cursor [skip ci]',
            'content': base64.b64encode(json.dumps(encrypt({'schema': 1, 'lastUpdateId': cursor}, self.key)).encode()).decode(),
        }
        if self.sha:
            payload['sha'] = self.sha
        record = self.github.api('/contents/data/telegram-commands.enc.json', 'PUT', payload)
        if not record or not record.get('content', {}).get('sha'):
            raise RuntimeError('Sauvegarde du curseur non confirmée.')
        self.sha = record['content']['sha']


def process(updates, chat_id, username, cursor, report, send, save):
    replies = 0
    persisted = cursor
    for update in updates:
        uid = update.get('update_id')
        if type(uid) is not int or uid < 0 or (cursor is not None and uid <= cursor):
            continue
        message = update.get('message') or {}
        chat = message.get('chat') or {}
        sender = message.get('from') or {}
        authorized = (chat.get('type') == 'private' and str(chat.get('id')) == chat_id
                      and str(sender.get('id')) == chat_id and not sender.get('is_bot'))
        text = message.get('text') or ''
        command = text.split()[0] if isinstance(text, str) and text.split() else ''
        if authorized and command.lower() in ('/logs', '/logs@' + username.lower()):
            if replies >= MAX_REPLIES:
                break
            send(report())  # Save only after Telegram confirms delivery; retry failures next run.
            replies += 1
            save(uid)
            persisted = uid
        cursor = uid
    if cursor is not None and cursor != persisted:
        save(cursor)
    return replies


def run():
    token, chat_id, key = (os.getenv(name, '').strip() for name in ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'UA_ENCRYPTION_KEY'])
    repo = os.getenv('GITHUB_REPOSITORY', '')
    if not token or not key or not re.fullmatch(r'[1-9]\d*', chat_id) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
        raise ValueError('Configuration des commandes manquante.')
    github = GitHubState(os.environ['GITHUB_TOKEN'], repo)
    store = CommandStore(github, key)
    cursor = store.load()
    bot = telegram(token, 'getMe', {})
    if not bot.get('is_bot') or not isinstance(bot.get('username'), str):
        raise ValueError('Identité du bot invalide.')
    updates = telegram(token, 'getUpdates', {'offset': cursor + 1 if cursor is not None else 0, 'limit': 100, 'timeout': 0, 'allowed_updates': ['message']})
    if not isinstance(updates, list):
        raise ValueError('Réponse de commandes invalide.')
    cache = []
    def report():
        if not cache:
            state, runs, state_ok, runs_ok = {}, [], True, True
            try:
                state = github.load(key)
                if not isinstance(state, dict):
                    raise ValueError()
            except Exception:
                state, state_ok = {}, False
            try:
                data = github.api('/actions/workflows/scan.yml/runs?per_page=5')
                runs = data['workflow_runs']
                if not isinstance(runs, list):
                    raise ValueError()
            except Exception:
                runs, runs_ok = [], False
            cache.append(diagnostics(state, runs, repo, state_ok=state_ok, runs_ok=runs_ok))
        return cache[0]
    def send(text):
        result = telegram(token, 'sendMessage', {'chat_id': chat_id, 'text': text, 'link_preview_options': {'is_disabled': True}})
        if type(result.get('message_id')) is not int or str(result.get('chat', {}).get('id')) != chat_id:
            raise RuntimeError('Livraison de la réponse non confirmée.')
    count = process(updates, chat_id, bot['username'], cursor, report, send, store.save)
    print(f'Commandes Telegram traitées : {count} réponse(s). Aucun scan UNIQLO lancé.')


if __name__ == '__main__':
    try:
        run()
    except Exception:
        print('Lecture des commandes Telegram en échec. Vérifiez les secrets, les droits GitHub et l’absence de webhook ou lecteur getUpdates concurrent. Aucun identifiant affiché.', file=sys.stderr)
        raise SystemExit(1)
