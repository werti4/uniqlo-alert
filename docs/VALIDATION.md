# Validation actuelle et preuves

Consolidation documentaire du **29 octobre 2026, Europe/Paris**, après `5fdd32a`. Les résultats ci-dessous sont datés ; ils ne constituent pas une nouvelle exécution des tests. État de référence : [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md). Anciennes préparations et blocages : [HISTORY.md](HISTORY.md), complétés par l’historique Git.

## Fonctionnement réel validé

| Vérification | Preuve | Portée |
| --- | --- | --- |
| Activation sécurisée | [40869512253](https://github.com/werti4/uniqlo-alert/actions/runs/40869512253), dernière tentative réussie, job `123439570029` | HMAC confirme concordance token/chat Actions et Worker ; identité privée, username, workflows actifs et dispatch PAT vérifiés sans lire les valeurs |
| Webhook Telegram | Même activation : `access_verified=true`, `dispatch_accepted=true`, `webhook_confirmed=true` | setWebhook/getWebhookInfo : `/telegram`, messages uniquement, une connexion, updates non supprimées |
| Commandes en attente | [40871565324](https://github.com/werti4/uniqlo-alert/actions/runs/40871565324), [40871569061](https://github.com/werti4/uniqlo-alert/actions/runs/40871569061), succès | Deux vraies commandes en attente traitées après activation ; aucun test envoyé par l’agent |
| Horaire naturel | [40872057387](https://github.com/werti4/uniqlo-alert/actions/runs/40872057387), créé à **12:17:34 UTC / 13:17:34 Paris** | Contrôle, installation et étape « Scanner les favoris » exécutés avec succès ; aucun scan forcé |
| Corrélation du cron | [40872060775](https://github.com/werti4/uniqlo-alert/actions/runs/40872060775), job `123441351584` | `VERIFY_ONLY=true`, `VERIFY_HOUR=498132`, `lastHourlyDispatch=498132`, `hourly_enabled=true`, `webhook_confirmed=true`, `pending_updates=0`, `last_error_date=null`, `queue_length=0` |
| Commandes après migration | [40873511528](https://github.com/werti4/uniqlo-alert/actions/runs/40873511528) à 13:28 et [40874426522](https://github.com/werti4/uniqlo-alert/actions/runs/40874426522) à 13:34 Paris, relus en lecture seule | Deux runs supplémentaires `workflow_dispatch` sur `5fdd32a`, terminés avec succès ; contenu privé non inspecté |
| Retour utilisateur | « Tout a l’air de bien marcher » après activation | Retour général positif ; pas une preuve séparée des trois commandes ou d’une vraie baisse reçue |

Les heures d’activation des anciens comptes rendus étaient arrondies ; le job final d’activation a terminé à **13:13:58 Paris**, avant le premier cron de 13:17.

## Configuration et migration validées

API Cloudflare : Worker déployé, route workers.dev, DO SQLite, migration/binding, cron `17 * * * *` et cinq secrets requis présents. Dernier état vérifié après le scan naturel : `HOURLY_SCAN_ENABLED=true`, `HOURLY_VERIFY_ENABLED=false`, `SETUP_ENABLED=false`, également dans wrangler.jsonc. Secret supplémentaire Cloudflare `UA_TELEGRAM_WEBHOOK_SECRET` inutilisé et conservé.

GitHub/Worker : URL racine concordante, `UA_TELEGRAM_ENABLED=true`, secret partagé identique, token/chat concordants, PAT ayant réussi les accès/dispatchs requis. Les valeurs ne sont pas lues ; les droits complets du PAT ne sont pas énumérés. La clé de chiffrement ne quitte pas Actions/Chrome.

Commit de migration `5fdd32a` : retrait des seuls `on.schedule` de scan.yml et telegram-commands.yml, après preuve naturelle. `workflow_dispatch`, on.push des favoris, permissions et concurrence `uniqlo-monitor` conservés. Commit `[skip actions]` pour éviter le scan de push lié à scan.yml. La tâche ponctuelle de contrôle de 13:25 a été désactivée après la validation ; aucun suivi supplémentaire annoncé.

Routes publiques testées avec `User-Agent: UniqloAlertBridge/1.0` : GET `/` → 404 JSON ; POST `/telegram` et `/pending` sans secret → 403 JSON. Le User-Agent applicatif corrige le refus Cloudflare 1010 observé avec urllib par défaut. Ne pas retirer cet en-tête du bridge et des outils de configuration.

## Validation du code

- Dernières suites locales avant consolidation : **68 tests Python et 33 tests Node réussis**, API/collecte simulées. Couverture : chiffrement compatible, concurrence, autorisation, catalogue partagé, file durable, déduplication, reprise après refus GitHub, accusé avant dispatch, horaire et activation sécurisée.
- CI [40869512226](https://github.com/werti4/uniqlo-alert/actions/runs/40869512226) réussie pour `197bbcb`, dont contrôle navigateur sous CSP et paquet Chrome. Les versions précédentes et leurs compteurs sont historiques.
- Wrangler **4.155.0**, dry-run du Worker avec setup réussi : bundle **13,63 Kio**, gzip **4,23 Kio**, DO conservé. Aucun nouveau déploiement nécessaire pour ce nettoyage documentaire.
- Workflows YAML parsés, scripts Python embarqués compilés, déclencheurs/concurrence et switches contrôlés lors de la migration.
- Version Chrome du dépôt **1.1.2**, paquet de **13 fichiers**, conservation des artefacts sept jours. Tests navigateur sur vrai HTML/CSP avec API Chrome simulées ; installation/rendu personnel distincts.

Nettoyage documentaire courant : liens locaux, cohérence avec catalogue/configuration/déclencheurs et `git diff --check` contrôlés avant publication. Aucune suite applicative relancée pour des fichiers Markdown seuls ; aucun scan, aucun message de test, aucune lecture des favoris en clair.

## Limites maintenues

Un run vert ne démontre pas que chaque article a été vérifié ; lire dates/erreurs dans Chrome ou `/favoris`. Un test Telegram réel antérieur a été reçu sur iPhone ([40804020828](https://github.com/werti4/uniqlo-alert/actions/runs/40804020828)), mais la future livraison d’une véritable alerte de baisse reste distincte. Les accusés et résultats actuels ne garantissent pas les horaires suivants ni l’absence de doublon après panne.

Le proxy cloud avait refusé une consultation directe UNIQLO avant réponse du site ; cela ne décrit pas les runners Actions. Stock/couleur/taille, offres membres et dates commerciales ne sont pas validés sur les fiches réelles.

Aucun abonnement créé/modifié, architecture compatible Free avec quotas du [guide Worker](../telegram-webhook/README.md). Lecture Billing refusée par OAuth : palier exact à consulter dans le tableau de bord si nécessaire, sans souscrire d’offre payante.
