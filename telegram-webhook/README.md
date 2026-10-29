# Récepteur Telegram par webhook — déploiement requis

Le service Cloudflare Workers + Durable Object SQLite reçoit Telegram immédiatement, persiste les commandes et déclenche GitHub Actions. Sa publication dans GitHub ne l’héberge pas. Palier gratuit possible sous réserve des quotas/conditions et de la disponibilité des Durable Objects SQLite sur le compte. Aucun abonnement payant à activer sans le vouloir.

L’accusé de réception devient rapide après déploiement ; le démarrage et la fin du scan restent soumis à l’attente GitHub. Cela ne répare pas le calendrier des scans périodiques. Une file persistante évite de perdre les commandes lorsque GitHub remplace un run en attente. Un rappel après 10 minutes retente une file non vidée, sans boucle permanente.

## Déploiement

Créer un compte Cloudflare. Depuis un terminal local avec Node.js >=22 :

```sh
cd telegram-webhook
npx wrangler@4.155.0 login
npx wrangler@4.155.0 deploy
```

Noter l’URL HTTPS du Worker. La configuration inclut la migration SQLite et aucun secret. Créer un PAT GitHub limité à `werti4/uniqlo-alert`, **Actions: Read and write**, sans droits Contents write ou administration, pour le déclenchement du workflow. Ne pas partager ce PAT en chat.

Créer un secret aléatoire de 32 à 256 caractères (lettres, chiffres, underscore et tiret) dans un gestionnaire de mots de passe. Enregistrer chaque valeur par saisie masquée :

```sh
npx wrangler@4.155.0 secret put WEBHOOK_SECRET
npx wrangler@4.155.0 secret put TELEGRAM_BOT_TOKEN
npx wrangler@4.155.0 secret put TELEGRAM_CHAT_ID
npx wrangler@4.155.0 secret put BOT_USERNAME
npx wrangler@4.155.0 secret put GITHUB_REPOSITORY
npx wrangler@4.155.0 secret put GITHUB_BRANCH
npx wrangler@4.155.0 secret put GITHUB_DISPATCH_TOKEN
```

Utiliser le secret aléatoire, le jeton Telegram **actuel**, son chat ID privé, le username du bot sans @, `werti4/uniqlo-alert`, `main` et le PAT dédié. Aucun accès à la clé AES des favoris n’est donné au Worker. Ne pas réutiliser un ancien jeton révoqué.

## Relier GitHub et Telegram

GitHub → Settings → Secrets and variables → Actions :

- Secret `UA_TELEGRAM_WEBHOOK_SECRET` : même valeur que WEBHOOK_SECRET.
- Variable `UA_TELEGRAM_WEBHOOK_URL` : URL HTTPS racine du Worker, sans /telegram ni slash final.
- Conserver `UA_TELEGRAM_ENABLED=true` et les secrets existants du runner.

Une fois l’URL définie, le workflow de commandes lit la file webhook et n’appelle plus getUpdates ; ses passages schedule sont ignorés. Attendre la fin de tout ancien lecteur getUpdates, puis, depuis la racine du dépôt :

```sh
python3 tools/register_telegram_webhook.py
```

Ce script demande les secrets sans affichage, teste l’accès à la file, enregistre le webhook avec le header secret officiel et confirme l’URL via getWebhookInfo. Il ne supprime aucun message en attente et ne lance pas de scan.

Envoyer **/logs** : constater l’accusé immédiat, un run automatique de **Commandes Telegram**, puis le diagnostic. Envoyer /scan uniquement pour scanner réellement. Ces validations réelles sont indispensables avant d’annoncer le système opérationnel.

## Limites et retour arrière

Accès réservé au header secret et à la conversation privée/propriétaire. File de 20 commandes, trois traitées par passage, un scan maximum par passage. Les commandes restent persistées malgré l’annulation de runs GitHub en attente. Un accusé peut exceptionnellement être répété après une panne ; un scan déjà consommé n’est pas rejoué automatiquement.

En cas d’échec : vérifier URL, secrets, compte Cloudflare, expiration/droits du PAT et workflow actif. Ne pas journaliser les tokens ou corps des requêtes.

Retour arrière : `python3 tools/register_telegram_webhook.py --remove`, puis vider la variable Actions UA_TELEGRAM_WEBHOOK_URL. Ne pas utiliser simultanément webhook et lecteur getUpdates. La file Worker n’est pas retransférée dans Telegram lors de ce retour arrière.
