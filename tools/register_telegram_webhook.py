"""Local setup: masked secrets, no scan, no credential URLs in output."""
import argparse
import getpass
import json
import re
import urllib.request
from urllib.parse import urlsplit


def api(token, method, data):
    req = urllib.request.Request(f'https://api.telegram.org/bot{token}/{method}',method='POST',data=json.dumps(data).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=20) as response:
        result=json.load(response)
    if result.get('ok') is not True:raise ValueError()
    return result['result']


def main():
    parser=argparse.ArgumentParser(description='Configurer le webhook Telegram sans afficher les secrets.')
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--remove',action='store_true')
    mode.add_argument('--check',action='store_true',help='Contrôles en lecture seule ; aucun webhook enregistré.')
    args=parser.parse_args()
    try:
        token=getpass.getpass('Jeton Telegram actuel : ').strip()
        if args.remove:
            api(token,'deleteWebhook',{'drop_pending_updates':False})
            print('Webhook retiré. Videz la variable Actions UA_TELEGRAM_WEBHOOK_URL pour rétablir le polling.')
            return 0
        url=input('URL HTTPS racine du Worker : ').strip().rstrip('/')
        p=urlsplit(url)
        if p.scheme!='https' or not p.netloc or p.username or p.password or p.path or p.query or p.fragment:raise ValueError()
        if args.check:
            info=api(token,'getWebhookInfo',{})
            confirmed=(info.get('url')==url+'/telegram' and info.get('allowed_updates')==['message'] and info.get('max_connections')==1)
            # Never print raw API errors, credential URLs or Telegram message contents.
            print('Webhook : ' + ('URL et paramètres confirmés.' if confirmed else 'URL ou paramètres non conformes.'))
            print('Updates Telegram en attente : ' + str(info.get('pending_update_count', 'indisponible')))
            print('Date de dernière erreur Telegram : ' + str(info.get('last_error_date', 'aucune enregistrée')))
            return 0 if confirmed else 1
        secret=getpass.getpass('WEBHOOK_SECRET déjà enregistré dans Cloudflare et GitHub : ').strip()
        if not re.fullmatch(r'[A-Za-z0-9_-]{32,256}',secret):raise ValueError()
        req=urllib.request.Request(url+'/pending',method='POST',data=b'{}',headers={'Content-Type':'application/json','X-Bridge-Secret':secret,'User-Agent':'UniqloAlertBridge/1.0'})
        with urllib.request.urlopen(req,timeout=20) as response:
            if not isinstance(json.load(response).get('commands'),list):raise ValueError()
        api(token,'setWebhook',{'url':url+'/telegram','secret_token':secret,'allowed_updates':['message'],'max_connections':1,'drop_pending_updates':False})
        info=api(token,'getWebhookInfo',{})
        if info.get('url')!=url+'/telegram' or info.get('allowed_updates')!=['message'] or info.get('max_connections')!=1:raise ValueError()
        print('Webhook enregistré, URL et paramètres confirmés. Une commande volontaire du propriétaire reste nécessaire pour valider la réception réelle.')
        return 0
    except Exception:
        print('Configuration non confirmée. Vérifiez URL, secrets et réseau. Aucun identifiant affiché.')
        return 1


if __name__=='__main__':raise SystemExit(main())
