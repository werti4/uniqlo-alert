# Telegram via Cloudflare — Worker déployé, activation des accès restante

## État courant — webhook et premier scan horaire naturel validés

Le **29 octobre 2026 à 13:15 Paris**, activation réussie avec les secrets corrigés : [workflow 40869512253](https://github.com/werti4/uniqlo-alert/actions/runs/40869512253), job 123439570029. Concordance des secrets/token/chat Actions et Worker, identité/username du bot, propriétaire privé, workflows actifs et PAT Actions write vérifiés. setWebhook/getWebhookInfo confirment /telegram, allowed_updates message, max_connections=1, sans suppression des updates. Deux commandes déjà en attente ont été livrées et les runs Commandes Telegram 40871565324 et 40871569061 ont réussi. Aucun message de test ni scan forcé par l’agent.

**Premier déclenchement naturel prouvé à 13:17 Paris (12:17 UTC)** : [scanner 40872057387](https://github.com/werti4/uniqlo-alert/actions/runs/40872057387), créé à 12:17:34 UTC, toutes les étapes dont « Scanner les favoris » exécutées avec succès. [Diagnostic horaire 40872060775](https://github.com/werti4/uniqlo-alert/actions/runs/40872060775), job 123441351584 : VERIFY_ONLY=true, VERIFY_HOUR=498132, lastHourlyDispatch=498132, hourly_enabled=true, webhook_confirmed=true, pending_updates=0, last_error_date=null, queue_length=0. L’heure correspond au scheduled naturel et au dispatch mémorisé par le DO ; ce n’est pas un scan lancé pour tester.

Après validation, **HOURLY_SCAN_ENABLED=true**, **HOURLY_VERIFY_ENABLED=false**, **SETUP_ENABLED=false** confirmés par API et maintenus dans wrangler.jsonc ; cron Cloudflare **17 * * * *** inchangé. Les anciens on.schedule de scan.yml et telegram-commands.yml sont retirés par cette publication pour éviter les doublons. workflow_dispatch, on.push des favoris, permissions et groupe uniqlo-monitor sont conservés. Publication avec **[skip actions]**, car modifier scan.yml déclencherait sinon un scan de push. Aucun workflow entier désactivé.

La vérification Automations créée pour 13:25 Paris a été **désactivée**, car le déclenchement naturel a été vérifié ici avant cette échéance. Aucune autre vérification persistante n’est annoncée. Le workflow dédié configure-cloudflare.yml reste disponible en lecture seule par défaut, sans déclencheur push ; /configure est fermé, /configuration-status exige le secret commun. Six noms de secrets (cinq requis + extra inutilisé), DO SQLite/bindings, favoris, clé AES et extension préservés.

Limites : ce premier succès ne garantit ni tous les horaires suivants ni une collecte réussie de chaque article ; consulter les dates/erreurs par article. La réception sur l’iPhone d’une véritable future alerte de baisse reste distincte de l’acceptation par Telegram. Aucun abonnement modifié ; architecture compatible Free avec quotas documentés, mais Billing n’est pas lisible via OAuth. Les anciens échecs de format sont résolus : ne pas redemander de recréer les secrets.

État vérifié le 29 octobre 2026 : `uniqlo-telegram-webhook` déployé sur
https://uniqlo-telegram-webhook.uniqlo-alert-werti4.workers.dev . Binding `INBOX` → `TelegramInbox`, migration `v1`, stockage **SQLite** confirmé par API. Cron `17 * * * *` enregistré, mais **HOURLY_SCAN_ENABLED=true** depuis validation des accès ; premier événement naturel confirmé à 13:17 Paris. Dernier contrôle API après saisie utilisateur : les cinq secrets requis sont présents au type `secret_text` ; validité des accès et concordance du secret partagé confirmées par le workflow dédié. Ne pas recommencer leur création sans motif. Le webhook Telegram est enregistré et confirmé. Les étapes de saisie plus bas sont une référence, pas à répéter pour ce compte.

Le connecteur Cloudflare permet upload du Worker, secrets, migrations, bindings, domaine et cron. Son OAuth ne permet pas de lire les abonnements (Billing). Aucun abonnement créé/modifié. Le connecteur GitHub ne gère pas les variables/secrets Actions et ne peut pas créer un PAT personnel. Les secrets Actions existants ne sont pas lisibles en clair. Ces limites nécessitent les saisies masquées ci-dessous ; aucun secret dans une conversation, un commit ou une capture.

## Architecture et commandes

Telegram → `/telegram` Cloudflare → header secret officiel + propriétaire privé → catalogue partagé → file persistante → accusé Telegram → dispatch automatique de `telegram-commands.yml` → `/pending` et `/ack` authentifiés → résultat privé depuis Actions.

Cloudflare ne déchiffre aucun favori. `UA_ENCRYPTION_KEY` reste exclusivement dans Chrome et Actions. La file conserve 20 commandes, en traite trois par passage (un scan maximum), déduplique les updates et retente le dispatch après dix minutes si elle n’est pas vidée. Un accusé peut exceptionnellement être répété après une panne ; un scan consommé n’est pas relancé automatiquement.

| Commande | Résultat après activation |
| --- | --- |
| `/logs` | Diagnostic et cinq derniers runs du scanner, sans scan ni logs bruts personnels |
| `/scan` | Accusé puis début et résultat du scan ; promotions déjà présentes lors de l’ajout incluses ; bilan incomplet explicite si vérifications manquantes |
| `/favoris` | Tous les favoris publiés, actifs et pausés, derniers prix datés, 🔴 en promotion et prix de référence disponible, données manquantes/erreurs signalées ; **aucun scan** |

Pour actualiser les prix, utiliser `/scan`, en complément du calendrier horaire. Le résultat attend éventuellement un runner GitHub. Ne pas promettre de démarrage immédiat ou de réussite de chaque scan.

**Toute future commande exige catalogue `commands.json`, routage Cloudflare, traitement, tests, documentation ET redéploiement du Worker. Une modification uniquement dans GitHub est incomplète.** Contrat détaillé : [TELEGRAM_COMMANDS.md](../docs/TELEGRAM_COMMANDS.md).

Les clients Python envoyant des requêtes au Worker utilisent `User-Agent: UniqloAlertBridge/1.0`. Le User-Agent par défaut de urllib a déclenché un refus Cloudflare 1010 lors du diagnostic. [Cloudflare recommande un identifiant d’application explicite](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/) sur workers.dev ; ne pas retirer cet en-tête du lecteur Actions ni du script de configuration. La livraison depuis les serveurs Telegram reste à valider séparément.

Relais courant pour Codex : [CODEX_HANDOFF.md](../docs/CODEX_HANDOFF.md). Les étapes ci-dessous restent la procédure générale ; les saisies déjà effectuées ne sont pas à répéter par défaut.

## 1. Vérifier le palier et préparer les deux accès

Dans [le tableau de bord du Worker](https://dash.cloudflare.com/6f5af3971fa548918e6b51e78c26a4c1/workers/services/view/uniqlo-telegram-webhook/production), vérifier que le compte reste sur **Workers Free**. Ne pas sélectionner d’offre payante. L’API a accepté le Worker et le DO SQLite sans souscription ; `usage_model=standard` n’est pas une preuve du palier de facturation.

Créer un [fine-grained PAT GitHub](https://github.com/settings/personal-access-tokens/new) :

- Resource owner : `werti4`.
- Repository access : **Only select repositories**, sélectionner uniquement `uniqlo-alert`.
- Repository permissions : **Actions: Read and write** ; Metadata read est ajouté automatiquement. Aucun Contents write, Secrets, Administration ni accès à d’autres dépôts.
- Choisir une expiration et prévoir son renouvellement. Conserver le PAT dans un gestionnaire de mots de passe.

Utiliser le **jeton Telegram actuel renouvelé**, conservé après révocation de l’ancien. Aucun ancien token apparu dans l’historique. Conserver les secrets Telegram déjà fonctionnels dans Actions ; le token saisi côté Cloudflare doit correspondre au token actuel du même bot. Si le token Actions est encore révoqué, le remplacer par saisie masquée dans les Settings GitHub. Ne pas toucher à `UA_ENCRYPTION_KEY`.

## 2. Saisir les cinq secrets Worker, sans affichage

Depuis le poste personnel, avec Git, Node.js >=22 et Python 3, dans le dépôt à jour :

```sh
git switch main
git pull --ff-only origin main
cd telegram-webhook
npx wrangler@4.155.0 login
npx wrangler@4.155.0 secret put WEBHOOK_SECRET
npx wrangler@4.155.0 secret put TELEGRAM_BOT_TOKEN
npx wrangler@4.155.0 secret put TELEGRAM_CHAT_ID
npx wrangler@4.155.0 secret put BOT_USERNAME
npx wrangler@4.155.0 secret put GITHUB_DISPATCH_TOKEN
npx wrangler@4.155.0 secret list
```

Chaque `secret put` ouvre une **saisie masquée**. Ne pas mettre la valeur dans la ligne de commande.

| Nom | Valeur à saisir dans le champ masqué |
| --- | --- |
| `WEBHOOK_SECRET` | Générer dans le gestionnaire de mots de passe **64 caractères aléatoires** parmi lettres, chiffres, `_` et `-` ; conserver exactement la même valeur pour GitHub et l’enregistrement Telegram |
| `TELEGRAM_BOT_TOKEN` | Jeton actuel renouvelé du bot |
| `TELEGRAM_CHAT_ID` | Identifiant numérique positif de votre conversation privée/propriétaire ; même compte que dans Actions |
| `BOT_USERNAME` | Nom d’utilisateur du bot, sans `@` |
| `GITHUB_DISPATCH_TOKEN` | PAT limité Actions write créé à l’étape 1 |

`GITHUB_REPOSITORY=werti4/uniqlo-alert` et `GITHUB_BRANCH=main` sont déjà déployés comme **variables non secrètes** dans wrangler.jsonc. Ne pas les recréer comme secrets du même nom.

Alternative sans CLI pour ces cinq valeurs : Worker → Settings → Variables and Secrets → Add → type **Secret**, nom exact puis valeur masquée → Deploy. Ne jamais ajouter `UA_ENCRYPTION_KEY` au Worker.

## 3. Relier Actions et arrêter le polling avant le webhook

Dans [Settings → Secrets and variables → Actions](https://github.com/werti4/uniqlo-alert/settings/secrets/actions) :

- Onglet **Secrets**, New repository secret : `UA_TELEGRAM_WEBHOOK_SECRET` = exactement le `WEBHOOK_SECRET` du gestionnaire de mots de passe.
- Onglet [Variables](https://github.com/werti4/uniqlo-alert/settings/variables/actions), New repository variable : `UA_TELEGRAM_WEBHOOK_URL` = `https://uniqlo-telegram-webhook.uniqlo-alert-werti4.workers.dev` (sans `/telegram` ni slash final).
- Vérifier la variable existante `UA_TELEGRAM_ENABLED=true`. Préserver les secrets `UA_ENCRYPTION_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

Dès que l’URL est définie, les nouveaux passages planifiés du lecteur sont ignorés et les dispatchs utilisent la file Cloudflare. Dans Actions, **attendre la fin de tout run Commandes Telegram déjà en cours ou en attente** : un ancien run peut avoir conservé les variables précédentes. Aucun getUpdates en parallèle du webhook. Ne pas lancer ce workflow manuellement pour tester : il pourrait consommer un ancien `/scan` en attente.

## 4. Enregistrer et contrôler Telegram, sans message de test

Depuis la racine du dépôt :

```sh
python3 tools/register_telegram_webhook.py
```

Sur Windows, `py -3` peut remplacer `python3`. Le script demande le token et le secret par saisie masquée, ainsi que l’URL racine ci-dessus. Il vérifie `/pending`, puis appelle `setWebhook` avec :

- URL : `https://uniqlo-telegram-webhook.uniqlo-alert-werti4.workers.dev/telegram` ;
- secret officiel `X-Telegram-Bot-Api-Secret-Token` ;
- `allowed_updates=["message"]`, `max_connections=1`, `drop_pending_updates=false`.

Il contrôle ensuite l’URL par `getWebhookInfo`. Aucun scan ni message de test n’est envoyé **par le script**. Attention : Telegram peut livrer des commandes authentiques déjà en attente après l’enregistrement ; elles seront alors traitées normalement. Si leur présence doit être examinée, utiliser d’abord le contrôle en lecture seule ci-dessous ; ne pas effacer leur file automatiquement.

Contrôle complémentaire en lecture seule depuis un terminal personnel (ne pas saisir le token dans une URL ou ligne de commande) :

```sh
python3 tools/register_telegram_webhook.py --check
```

L’URL doit être celle de `/telegram`, les updates `message`, connexions 1. Ce mode ne modifie rien, demande le jeton par saisie masquée et n’affiche aucune réponse brute. Un ancien `last_error_date` ne prouve pas une erreur actuelle ; vérifier qu’il n’avance plus après réception réelle. Ne pas afficher `last_error_message` ou une réponse brute pouvant contenir des informations personnelles. À cette étape, une commande réelle envoyée volontairement par le propriétaire permettra de confirmer accusé, dispatch, résultat et vidage de la file ; l’agent n’en envoie pas sans demande.

## 5. Activer le calendrier horaire et terminer la migration

Après les accès et la liaison configurés, modifier **dans `telegram-webhook/wrangler.jsonc`** `HOURLY_SCAN_ENABLED` de `"false"` à `"true"`, puis depuis ce dossier :

```sh
npx wrangler@4.155.0 deploy --dry-run
npx wrangler@4.155.0 deploy
```

Publier également ce changement sur main, après récupération des nouvelles publications Chrome. Ne pas se limiter au tableau de bord sans maintenir la valeur dans le fichier : un futur déploiement pourrait sinon rétablir false. Les secrets Worker existants sont conservés par Wrangler.

Cron `17 * * * *` : une demande de `scan.yml` chaque heure à la minute 17, UTC comme Paris, **24 demandes par jour**. La propagation peut prendre plusieurs minutes. L’événement est dédupliqué après dispatch confirmé. GitHub l’affiche comme `workflow_dispatch`, ce qui ne signifie pas que l’utilisateur l’a lancé manuellement.

Attendre le **prochain déclenchement naturel** : constater le Scheduled Cloudflare et le run scanner correspondant. Aucun scan artificiel pour cette validation. Si le runner tarde, ne pas annoncer une panne ou une garantie de délai ; vérifier les états et erreurs.

**Après validation du fonctionnement Cloudflare**, retirer uniquement les blocs `on.schedule` de `.github/workflows/scan.yml` et `.github/workflows/telegram-commands.yml`. Conserver `workflow_dispatch`, les déclenchements de publication des favoris, les permissions et le groupe `uniqlo-monitor`. Ne pas désactiver les workflows entiers. Important : modifier scan.yml est lui-même un déclencheur de scan au push ; pour cette seule migration sans scan de test, utiliser un commit avec `[skip actions]`, après tests locaux, puis vérifier les deux workflows conservés. Les deux anciens calendriers ont été retirés après le scan naturel 40872057387 ; cette consigne décrit la procédure générale de migration.

## Quotas gratuits et limites réelles

Références consultées le 29/10/2026 : [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/), [DO pricing](https://developers.cloudflare.com/durable-objects/platform/pricing/), [Cron](https://developers.cloudflare.com/workers/configuration/cron-triggers/), [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

| Ressource sur Free | Quota documenté |
| --- | --- |
| Worker | 100 000 requêtes/jour, 10 ms de CPU par invocation (l’attente réseau est distincte) |
| Durable Objects | 100 000 requêtes/jour, 13 000 GB-s de durée/jour |
| Stockage DO SQLite | 5 millions de lignes lues/jour, 100 000 écrites/jour, 5 Go au total |

Les limites quotidiennes sont partagées au niveau du compte et se réinitialisent à 00:00 UTC. Sur Workers Free, dépassement = erreurs/refus ; aucun passage automatique à une offre payante n’a été demandé. Les commandes, appels de file et alarmes s’ajoutent aux événements horaires. Une petite charge personnelle est compatible, sans service illimité ni disponibilité garantie.

Le dépôt est **public**, et ses workflows utilisent les runners standards `ubuntu-latest`, dont le calcul est gratuit sur les dépôts publics. Ne pas généraliser cette gratuité aux larger runners ou à un futur dépôt privé. GitHub Free inclut 500 Mo d’artefacts (partagés avec Packages) et 10 Go de cache par dépôt ; les comptes et budgets réels sont à vérifier dans les Settings. Les artefacts de l’extension expirent après sept jours. Aucun runner payant ni option de stockage payante ajoutés.

## Mise à jour et retour arrière

Avant publication : récupérer origin/main, intégrer les publications de favoris concurrentes sans les écraser, ne jamais fusionner monitor-data dans main. Tests Python/Node et Wrangler dry-run ; publier puis déployer les mêmes sources. Aucune mise à jour automatique Cloudflare depuis GitHub n’est configurée.

Pour revenir à la version précédente du Worker : `npx wrangler@4.155.0 rollback <VERSION_ID>` après vérification des migrations/bindings et secrets compatibles. Le premier déploiement n’a pas de version précédente. Ne pas supprimer le namespace SQLite pour revenir en arrière.

Pour abandonner le webhook : désactiver HOURLY_SCAN_ENABLED dans le fichier et redéployer, exécuter `python3 tools/register_telegram_webhook.py --remove` (ne supprime pas les updates), attendre la fin des lecteurs webhook, puis vider UA_TELEGRAM_WEBHOOK_URL. Rétablir au besoin un seul calendrier GitHub de polling/scans. Ne jamais utiliser simultanément getUpdates et webhook. Les commandes déjà dans le DO ne sont pas retransférées dans Telegram ; conserver la file et traiter leur sort avant un basculement. Clé, favoris et historique chiffrés inchangés.

## Activation depuis iPhone sans terminal — préparation du 29 octobre 2026

L’utilisateur demande désormais de terminer ici avec le connecteur Cloudflare, sans terminal ni secret dans le chat. Le blocage de la conversation Codex dépourvue de connecteur ne s’applique pas à celle-ci. Ne recréer ni Worker ni secrets.

Procédure préparée : workflow dédié configure-cloudflare.yml + tools/configure_cloudflare.py + routes /configure (temporaires, SETUP_ENABLED=true et SETUP_EXPIRES_AT futur requis) et /configuration-status (lecture seule), toutes authentifiées par X-Bridge-Secret. Actions utilise ses secrets existants et envoie une preuve HMAC du jeton/chat ; le Worker vérifie la concordance, getMe/getChat, le username, les workflows actifs et l’absence de lecteur Commandes Telegram en cours. Le PAT Worker doit réussir un dispatch du seul workflow de diagnostic en verify_only=true pour prouver Actions write ; aucun scan ou message de test. Puis setWebhook est appelé sans supprimer les updates, et getWebhookInfo vérifie URL/allowed_updates/max_connections. Aucun accès à UA_ENCRYPTION_KEY dans cette procédure.

État à cet instant : code préparé/testé, résultat de configuration réelle encore à confirmer. SETUP_ENABLED et HOURLY_VERIFY_ENABLED sont false par défaut dans les sources ; l’activation temporaire est faite via le connecteur en conservant tous les secrets avec inherit strict. Fermer SETUP_ENABLED après l’essai. Ne passer HOURLY_SCAN_ENABLED à true qu’après succès attesté du workflow. Le switch temporaire HOURLY_VERIFY_ENABLED permet au prochain horaire naturel de déclencher un diagnostic en lecture seule, avec l’heure du dispatch mémorisée dans le DO. Après validation, désactiver ce switch, retirer les anciens on.schedule GitHub et le déclencheur push d’activation ; conserver workflow_dispatch et les workflows scanner/commandes.

Le commit de préparation ne touche ni scanner, ni scan.yml, ni favoris/extension. Les contrôles simulés passent ; aucun vrai scan ni message de test n’est envoyé pour développer cette procédure. Le statut réel et les étapes restantes doivent être actualisés après l’essai.
