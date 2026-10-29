# Telegram via Cloudflare — exploitation et maintenance

## État déployé

Configuration terminée le **29 octobre 2026**. Worker **[uniqlo-telegram-webhook](https://uniqlo-telegram-webhook.uniqlo-alert-werti4.workers.dev)**, webhook `/telegram`, DO **SQLite** (`INBOX` → `TelegramInbox`, migration `v1`). Cron **`17 * * * *`** : une demande de scan par heure à la minute 17. Premier déclenchement naturel validé à **13:17 Paris / 12:17 UTC** ; anciens calendriers GitHub ensuite retirés dans `5fdd32a`.

`HOURLY_SCAN_ENABLED=true`, `HOURLY_VERIFY_ENABLED=false`, `SETUP_ENABLED=false` dans le déploiement vérifié et `wrangler.jsonc`. **Aucune activation ni création de secrets à répéter.** [Contexte de référence](../docs/PROJECT_CONTEXT.md), [preuves datées](../docs/VALIDATION.md), [reprise Codex](../docs/CODEX_HANDOFF.md).

## Architecture et commandes

Telegram → `/telegram` Cloudflare → secret officiel + propriétaire privé → catalogue partagé → file persistante → accusé → dispatch automatique de `telegram-commands.yml` → `/pending` et `/ack` authentifiés → résultat privé depuis Actions.

Cloudflare ne déchiffre aucun favori. `UA_ENCRYPTION_KEY` reste exclusivement dans Chrome et Actions. La file conserve 20 commandes, en traite trois par passage (un scan maximum), déduplique les updates et retente le dispatch après dix minutes si elle n’est pas vidée. Une interruption après envoi mais avant sauvegarde peut exceptionnellement produire un doublon ; un scan consommé n’est pas relancé automatiquement.

| Commande | Résultat |
| --- | --- |
| `/logs` | Diagnostic et cinq derniers runs du scanner, sans scan ni logs bruts personnels |
| `/scan` | Accusé, état puis résultat du scan ; promotions déjà présentes lors de l’ajout incluses ; bilan incomplet explicite si vérifications manquantes |
| `/favoris` | Tous les favoris publiés, actifs et pausés, derniers prix datés, 🔴 promotion et prix de référence disponible, données manquantes/erreurs signalées ; **aucun scan** |

Pour actualiser les prix, utiliser `/scan`, en complément du calendrier horaire. L’accusé vient du Worker ; le résultat peut attendre un runner GitHub. Aucun démarrage immédiat ni succès de chaque scan garanti. Les dispatchs automatiques apparaissent comme `workflow_dispatch` dans GitHub.

**Toute future commande exige catalogue `commands.json`, routage Cloudflare, traitement, tests, documentation ET déploiement du Worker.** Contrat : [TELEGRAM_COMMANDS.md](../docs/TELEGRAM_COMMANDS.md). Une publication GitHub seule ne met pas le Worker à jour.

## Variables et secrets existants

| Service / type | Nom | Rôle, jamais la valeur secrète |
| --- | --- | --- |
| Worker / variables | `GITHUB_REPOSITORY`, `GITHUB_BRANCH` | `werti4/uniqlo-alert`, `main` |
| Worker / variables | `HOURLY_SCAN_ENABLED`, `HOURLY_VERIFY_ENABLED`, `SETUP_ENABLED` | Respectivement `true`, `false`, `false` |
| Worker / secret | `WEBHOOK_SECRET` | Secret robuste partagé avec Actions et l’authentification officielle Telegram |
| Worker / secrets | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `BOT_USERNAME` | Bot actuel renouvelé, propriétaire privé autorisé et username sans `@` |
| Worker / secret | `GITHUB_DISPATCH_TOKEN` | PAT limité au dépôt, Actions lecture/écriture ; prévoir son expiration |
| Actions / variables | `UA_TELEGRAM_WEBHOOK_URL`, `UA_TELEGRAM_ENABLED` | URL **racine** du Worker sans `/telegram` ni slash final ; `true` |
| Actions / secret | `UA_TELEGRAM_WEBHOOK_SECRET` | Exactement le `WEBHOOK_SECRET` du Worker |
| Actions / secrets | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Concordants avec Worker |
| Actions + Chrome / clé | `UA_ENCRYPTION_KEY` | Clé existante des favoris ; **jamais Worker**, ne pas régénérer |

Un secret Cloudflare supplémentaire nommé `UA_TELEGRAM_WEBHOOK_SECRET` a été saisi ; il est inutilisé et conservé. Le nom lu par le Worker est `WEBHOOK_SECRET`. Les contrôles sécurisés ont validé la concordance et les accès nécessaires sans relire les valeurs. Aucun ancien jeton révoqué à reprendre dans l’historique.

## Contrôle et maintenance depuis iPhone

Aucune opération n’est nécessaire pour continuer à utiliser les commandes. Pour consulter les exécutions, ouvrir [Actions](https://github.com/werti4/uniqlo-alert/actions) dans Safari ; l’événement `workflow_dispatch` peut venir de Cloudflare et ne signifie pas un lancement manuel.

Pour une vérification administrative en lecture seule : ouvrir [Configurer Cloudflare sans scan](https://github.com/werti4/uniqlo-alert/actions/workflows/configure-cloudflare.yml), toucher **Run workflow**, branche **main**, laisser **verify_only** coché (`true`) et le champ **hour** vide, puis lancer et lire le résumé. Ce diagnostic appelle `/configuration-status`, sans scan ni message Telegram. Il ne faut pas lancer **Commandes Telegram** pour tester : cela pourrait traiter un vrai `/scan` en attente.

Si un secret doit un jour être renouvelé :

1. Worker : [tableau de bord](https://dash.cloudflare.com/6f5af3971fa548918e6b51e78c26a4c1/workers/services/view/uniqlo-telegram-webhook/production) → **Settings → Runtime variables and secrets → Production** → crayon du secret → **Rotate** → saisie privée → **Deploy**. Une valeur chiffrée n’est pas relisible ; son masquage est normal.
2. GitHub : [Secrets Actions](https://github.com/werti4/uniqlo-alert/settings/secrets/actions) → crayon du secret concerné → nouvelle valeur → **Update secret**. [Variables Actions](https://github.com/werti4/uniqlo-alert/settings/variables/actions) est un onglet séparé. Ne pas toucher à la clé de favoris.
3. Conserver la concordance entre services. `WEBHOOK_SECRET` doit contenir **32 à 256 caractères** autorisés par l’outil, uniquement lettres/chiffres/`_`/`-` ; recommandation : **64 caractères aléatoires** générés dans un gestionnaire privé. Il est distinct du token BotFather. Ne rien coller dans le chat.
4. Une rotation du token/secret de webhook exige aussi une réinscription Telegram contrôlée ; ne pas la confondre avec une simple mise à jour de variable. Demander au connecteur de préparer l’opération avec les secrets déjà stockés.

Les noms d’onglets peuvent être tronqués sur iPhone : faire défiler horizontalement jusqu’à **Settings**, puis revenir en haut de la page. Le profil utilisateur Cloudflare n’est pas la page de réglages du Worker.

## Administration sécurisée du webhook

`configure-cloudflare.yml` + `tools/configure_cloudflare.py` utilisent les secrets Actions existants. `verify_only=true` appelle `/configuration-status`, protégé par `X-Bridge-Secret`. Pour une **réinscription nécessaire et autorisée**, le connecteur ouvre temporairement `/configure` avec `SETUP_ENABLED=true` et `SETUP_EXPIRES_AT` futur ; il faut ensuite lancer le workflow en `verify_only=false`, contrôler le résultat, puis refermer le switch. Ne pas ouvrir cette route pour une simple lecture.

L’activation vérifie une preuve HMAC token/chat, getMe/getChat, username/propriétaire privé, workflows actifs et absence d’ancien lecteur. Le PAT Worker doit réussir un dispatch du seul diagnostic en lecture seule, sans scanner. Ensuite setWebhook/getWebhookInfo confirment : URL racine + `/telegram`, secret officiel `X-Telegram-Bot-Api-Secret-Token`, `allowed_updates=["message"]`, `max_connections=1`, `drop_pending_updates=false`. Les vraies commandes déjà en attente peuvent alors être livrées normalement ; aucun effacement automatique.

`HOURLY_VERIFY_ENABLED` est un switch de diagnostic temporaire : il associe au prochain cron naturel une lecture d’état avec son heure mémorisée. Il reste **false** en exploitation. `SETUP_ENABLED` reste **false** après l’intervention. Les bindings secrets sont préservés lors des mises à jour API (`inherit`), sans lire leur contenu ni modifier la migration SQLite.

Sur poste de développement, `tools/register_telegram_webhook.py --check` est une alternative en lecture seule, avec saisie masquée. Le script sans option enregistre le webhook ; `--remove` le retire sans supprimer les updates. Ce terminal est facultatif, non requis pour l’utilisateur sur iPhone.

Les clients Python conservent `User-Agent: UniqloAlertBridge/1.0` : le User-Agent par défaut de urllib a provoqué un refus Cloudflare 1010. [Recommandation Cloudflare](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/). Ne pas afficher les réponses Telegram brutes ou URL contenant un token dans les erreurs.

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

Récupérer `origin/main` avant publication et intégrer les nouvelles publications Chrome sans les écraser. Préserver `monitor-data`, la clé et les réglages. Tester les changements applicatifs selon [DEVELOPMENT.md](../docs/DEVELOPMENT.md). Depuis `telegram-webhook/`, pour le développeur disposant d’un poste :

```sh
npx wrangler@4.155.0 deploy --dry-run
npx wrangler@4.155.0 deploy
```

Le connecteur Cloudflare est l’alternative sans terminal. Publier et déployer les mêmes sources, conserver secrets/bindings/migration et la valeur réelle des switches. Aucun déploiement automatique GitHub → Cloudflare n’est installé. Vérifier le résultat et les routes, sans scan ou message de test imposé.

Les anciens `on.schedule` GitHub ont été retirés **après** le scan naturel validé. Ne pas les rétablir en parallèle de Cloudflare. `workflow_dispatch`, on.push des favoris et concurrence `uniqlo-monitor` restent nécessaires. Une modification de scan.yml peut elle-même déclencher un scan au push : respecter l’interdiction de scan forcé et utiliser `[skip actions]` pour une maintenance devant l’éviter, après contrôles adaptés.

Pour restaurer une version du Worker : contrôler la compatibilité des bindings/secrets/migrations et utiliser le rollback du connecteur ou `npx wrangler@4.155.0 rollback <VERSION_ID>`. Ne pas supprimer le namespace SQLite.

Pour revenir au polling : désactiver `HOURLY_SCAN_ENABLED` dans les sources et le déploiement, retirer le webhook **sans supprimer les updates**, attendre les lecteurs webhook, puis vider `UA_TELEGRAM_WEBHOOK_URL`. Rétablir un seul calendrier GitHub si nécessaire. Jamais getUpdates et webhook simultanés. Les commandes du DO ne sont pas retransférées à Telegram : conserver sa file et décider de leur traitement avant basculement. Aucun changement de clé, favoris ou historique chiffrés.
