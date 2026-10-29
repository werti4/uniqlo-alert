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
    parser.add_argument('--remove',action='store_true')
    args=parser.parse_args()
    try:
        token=getpass.getpass('Jeton Telegram actuel : ').strip()
        if args.remove:
            api(token,'deleteWebhook',{'drop_pending_updates':False})
            print('Webhook retiré. Videz la variable Actions UA_TELEGRAM_WEBHOOK_URL pour rétablir le polling.')
            return 0
        url=input('URL HTTPS racine du Worker : ').strip().rstrip('/')
        secret=getpass.getpass('WEBHOOK_SECRET déjà enregistré dans Cloudflare et GitHub : ').strip()
        p=urlsplit(url)
        if p.scheme!='https' or not p.netloc or p.username or p.password or p.path or p.query or p.fragment or not re.fullmatch(r'[A-Za-z0-9_-]{32,256}',secret):raise ValueError()
        req=urllib.request.Request(url+'/pending',method='POST',data=b'{}',headers={'Content-Type':'application/json','X-Bridge-Secret':secret})
        with urllib.request.urlopen(req,timeout=20) as response:
            if not isinstance(json.load(response).get('commands'),list):raise ValueError()
        api(token,'setWebhook',{'url':url+'/telegram','secret_token':secret,'allowed_updates':['message'],'max_connections':1,'drop_pending_updates':False})
        if api(token,'getWebhookInfo',{}).get('url')!=url+'/telegram':raise ValueError()
        print('Webhook enregistré et URL confirmée. Envoyez /logs au bot pour tester la réception réelle.')
        return 0
    except Exception:
        print('Configuration non confirmée. Vérifiez URL, secrets et réseau. Aucun identifiant affiché.')
        return 1


if __name__=='__main__':raise SystemExit(main())
