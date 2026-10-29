# Reprise Codex — Cloudflare / Telegram activés

## État courant — webhook et premier scan horaire naturel validés

Le **29 octobre 2026 à 13:15 Paris**, activation réussie avec les secrets corrigés : [workflow 40869512253](https://github.com/werti4/uniqlo-alert/actions/runs/40869512253), job 123439570029. Concordance des secrets/token/chat Actions et Worker, identité/username du bot, propriétaire privé, workflows actifs et PAT Actions write vérifiés. setWebhook/getWebhookInfo confirment /telegram, allowed_updates message, max_connections=1, sans suppression des updates. Deux commandes déjà en attente ont été livrées et les runs Commandes Telegram 40871565324 et 40871569061 ont réussi. Aucun message de test ni scan forcé par l’agent.

**Premier déclenchement naturel prouvé à 13:17 Paris (12:17 UTC)** : [scanner 40872057387](https://github.com/werti4/uniqlo-alert/actions/runs/40872057387), créé à 12:17:34 UTC, toutes les étapes dont « Scanner les favoris » exécutées avec succès. [Diagnostic horaire 40872060775](https://github.com/werti4/uniqlo-alert/actions/runs/40872060775), job 123441351584 : VERIFY_ONLY=true, VERIFY_HOUR=498132, lastHourlyDispatch=498132, hourly_enabled=true, webhook_confirmed=true, pending_updates=0, last_error_date=null, queue_length=0. L’heure correspond au scheduled naturel et au dispatch mémorisé par le DO ; ce n’est pas un scan lancé pour tester.

Après validation, **HOURLY_SCAN_ENABLED=true**, **HOURLY_VERIFY_ENABLED=false**, **SETUP_ENABLED=false** confirmés par API et maintenus dans wrangler.jsonc ; cron Cloudflare **17 * * * *** inchangé. Les anciens on.schedule de scan.yml et telegram-commands.yml sont retirés par cette publication pour éviter les doublons. workflow_dispatch, on.push des favoris, permissions et groupe uniqlo-monitor sont conservés. Publication avec **[skip actions]**, car modifier scan.yml déclencherait sinon un scan de push. Aucun workflow entier désactivé.

La vérification Automations créée pour 13:25 Paris a été **désactivée**, car le déclenchement naturel a été vérifié ici avant cette échéance. Aucune autre vérification persistante n’est annoncée. Le workflow dédié configure-cloudflare.yml reste disponible en lecture seule par défaut, sans déclencheur push ; /configure est fermé, /configuration-status exige le secret commun. Six noms de secrets (cinq requis + extra inutilisé), DO SQLite/bindings, favoris, clé AES et extension préservés.

Limites : ce premier succès ne garantit ni tous les horaires suivants ni une collecte réussie de chaque article ; consulter les dates/erreurs par article. La réception sur l’iPhone d’une véritable future alerte de baisse reste distincte de l’acceptation par Telegram. Aucun abonnement modifié ; architecture compatible Free avec quotas documentés, mais Billing n’est pas lisible via OAuth. Les anciens échecs de format sont résolus : ne pas redemander de recréer les secrets.

## Références et préservation

Lire AGENTS.md, PROJECT_CONTEXT.md, TELEGRAM_COMMANDS.md, DEVELOPMENT.md et telegram-webhook/README.md depuis la dernière main. Dépôt werti4/uniqlo-alert ; récupérer les publications Chrome avant chaque commit, ne pas forcer la tête GitHub. Aucun autre dépôt/prototype à recréer.

Worker uniqlo-telegram-webhook, compte 6f5af3971fa548918e6b51e78c26a4c1, URL racine https://uniqlo-telegram-webhook.uniqlo-alert-werti4.workers.dev. INBOX → TelegramInbox, migration v1 SQLite, namespace 84ca5eaff5764f178aa74c2854fd70be. Cron 17 * * * * UTC, minute 17 également à Paris.

Cinq secrets attendus déjà présents et validés par la procédure : WEBHOOK_SECRET, TELEGRAM_BOT_TOKEN actuel renouvelé, TELEGRAM_CHAT_ID propriétaire privé, BOT_USERNAME sans @, GITHUB_DISPATCH_TOKEN (Actions read/write limité au dépôt attendu). Extra UA_TELEGRAM_WEBHOOK_SECRET côté Cloudflare inutilisé, ne pas le confondre avec WEBHOOK_SECRET. Ne recréer ni Worker, ni secrets. Ne jamais afficher/lire les valeurs.

GitHub : UA_TELEGRAM_WEBHOOK_URL = racine, UA_TELEGRAM_ENABLED=true, secret UA_TELEGRAM_WEBHOOK_SECRET identique à WEBHOOK_SECRET, TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID concordants avec Cloudflare. UA_ENCRYPTION_KEY reste exclusivement dans Actions/Chrome, aucune transmission au Worker. Favoris main:data/watchlist.enc.json et historique monitor-data:data/state.enc.json préservés, aucun déchiffrement par l’agent.

## Fonctionnement et limites

Telegram → webhook Cloudflare → secret officiel + propriétaire privé → catalogue commands.json → file durable → accusé → dispatch GitHub → résultat privé. GitHub reste le moteur ; délai de runner et erreurs externes restent possibles. Le Worker déduplique les updates, garde la file (20 commandes, trois par passage, un scan maximum), réessaie les dispatchs après dix minutes. Aucun lancement manuel utilisateur normalement requis.

- /logs : diagnostic et dernières exécutions, sans scan.
- /scan : demande explicite du propriétaire, progression/bilan des promotions, y compris celles présentes dès l’ajout. Résultat incomplet explicite si erreurs/différés/prix de base absent.
- /favoris : tous les favoris publiés, derniers prix datés, 🔴 en promotion, prix de référence disponible et données manquantes signalées. Aucun scan ; /scan permet d’actualiser.

Toute future commande exige catalogue + routage Cloudflare + traitement + tests + documentation + déploiement Worker. Un commit GitHub seul ne déploie pas Cloudflare. Aucun pipeline automatique de déploiement Worker installé.

## Outils et activation administrative

Le connecteur Cloudflare de cette conversation permet lecture/configuration/déploiement ; Billing OAuth refusé. Le connecteur GitHub ne lit/gère pas les paramètres secrets/variables Actions. La validation s’est faite dans les runtimes sécurisés via tools/configure_cloudflare.py et workflow configure-cloudflare.yml, sans exporter de secrets. /configure est fermé par SETUP_ENABLED=false ; son ouverture exige aussi SETUP_EXPIRES_AT futur. /configuration-status est en lecture seule et exige X-Bridge-Secret. Le workflow dédié conserve workflow_dispatch, vérification seule par défaut ; son déclencheur push temporaire a été retiré. Ne pas le confondre avec le workflow de commandes.

Pour une nouvelle vérification avec les secrets actuels, utiliser uniquement le workflow dédié en verify_only=true ; aucune émission Telegram, aucun scan. Les clients Python doivent conserver User-Agent UniqloAlertBridge/1.0 pour workers.dev (urllib par défaut était bloqué 1010). Ne pas appeler getUpdates en parallèle du webhook.

Git fetch HTTPS fonctionne ; push direct a échoué faute d’identifiants, gh non installé. Publication possible via GitHub create_tree(base tree)/create_commit(parent main)/update_ref(expected_sha, force=false). Si main bouge, intégrer ses nouvelles données. Checkout observé /workspace/scratch/6e97d4083c7f/uniqlo-alert, chemin à revérifier dans une autre conversation. Si un connecteur n’y est pas exposé, ne pas prétendre conserver les accès de celle-ci.

Tests du code de configuration : 68 Python / 33 Node et CI du commit 197bbcb réussis, simulations sans scan/message réel. Les échecs antérieurs du secret (caractères puis longueur) sont résolus par la preuve de succès actuelle. Ne plus demander cette correction sur la base d’anciens paragraphes.

Gratuité : pas d’offre payante souscrite ; architecture compatible Free avec quotas réels documentés dans le README, sans service illimité. Retour arrière : désactiver l’horaire, retirer le webhook sans drop des updates, attendre les lecteurs, vider l’URL Actions puis ne rétablir qu’un polling/calendrier. Conserver la file DO, la clé et les données chiffrées.
