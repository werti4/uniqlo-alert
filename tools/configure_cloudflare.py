"""Actions-only setup: existing secrets stay in secure runtimes, never in output."""
import hashlib
import hmac
import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = 'https://uniqlo-telegram-webhook.uniqlo-alert-werti4.workers.dev'


def run():
    required = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'UA_TELEGRAM_WEBHOOK_SECRET']
    missing = [name for name in required if not os.getenv(name, '').strip()]
    if missing:
        raise ValueError('Secrets Actions manquants : ' + ', '.join(missing))
    if os.getenv('GITHUB_REPOSITORY') != 'werti4/uniqlo-alert' or os.getenv('GITHUB_REF') != 'refs/heads/main':
        raise ValueError('Exécution sur main du dépôt attendu requise.')
    if os.getenv('UA_TELEGRAM_WEBHOOK_URL', '').rstrip('/') != ROOT:
        raise ValueError('Variable Actions UA_TELEGRAM_WEBHOOK_URL incorrecte ou absente.')
    if os.getenv('UA_TELEGRAM_ENABLED') != 'true':
        raise ValueError('Variable Actions UA_TELEGRAM_ENABLED doit valoir true.')
    secret = os.environ['UA_TELEGRAM_WEBHOOK_SECRET'].strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]{32,256}', secret):
        raise ValueError('Format du secret webhook incorrect : 32 à 256 lettres/chiffres/_/-.')
    verify_only = os.getenv('VERIFY_ONLY') == 'true'
    payload = {} if verify_only else {'root': ROOT, 'enabled': True, 'proof': hmac.new(secret.encode(), (os.environ['TELEGRAM_BOT_TOKEN'].strip()+'\n'+os.environ['TELEGRAM_CHAT_ID'].strip()).encode(), hashlib.sha256).hexdigest()}
    request = urllib.request.Request(ROOT + ('/configuration-status' if verify_only else '/configure'), data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json', 'User-Agent': 'UniqloAlertBridge/1.0', 'X-Bridge-Secret': secret}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        # Only report known enum codes; never raw upstream API messages/URLs.
        allowed = {'repository_configuration','secret_format','github_cloudflare_values_differ','bot_username_mismatch','private_owner_mismatch','workflow_inactive','old_command_reader_running','other_webhook_present','webhook_not_confirmed','github_access_unavailable','telegram_getMe_unavailable','telegram_getChat_unavailable','telegram_getWebhookInfo_unavailable','telegram_setWebhook_unavailable'}
        try:
            code = json.load(error).get('error')
        except Exception:
            code = None
        raise ValueError('Contrôle Cloudflare refusé : ' + (code if code in allowed else 'accès/secret ou activation temporaire à vérifier')) from None
    except Exception:
        raise ValueError('Worker indisponible ; aucun identifiant affiché.') from None
    if result.get('ok') is not True or result.get('webhook_confirmed') is not True:
        raise ValueError('Webhook non confirmé ; aucun scan lancé.')
    hour = os.getenv('VERIFY_HOUR', '').strip()
    if hour and (not hour.isdigit() or type(result.get('lastHourlyDispatch')) is not int or result['lastHourlyDispatch'] < int(hour)):
        raise ValueError('Dispatch horaire naturel non confirmé.')
    safe = {name: result.get(name) for name in ['access_verified','dispatch_accepted','webhook_confirmed','pending_updates','last_error_date','hourly_enabled','lastHourlyDispatch','queue_length'] if name in result}
    print('Configuration Cloudflare — contrôles sans scan/message de test : ' + json.dumps(safe))
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as output:
            output.write('Configuration Cloudflare : contrôles confirmés.\n\n```json\n'+json.dumps(safe, indent=2)+'\n```\n')


if __name__ == '__main__':
    try:
        run()
    except ValueError as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
