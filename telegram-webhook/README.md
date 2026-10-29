# Telegram via Cloudflare — Worker déployé, activation des accès restante

État vérifié le 29 octobre 2026 : `uniqlo-telegram-webhook` déployé sur
https://uniqlo-telegram-webhook.uniqlo-alert-werti4.workers.dev . Binding `INBOX` → `TelegramInbox`, migration `v1`, stockage **SQLite** confirmé par API. Cron `17 * * * *` enregistré, mais **HOURLY_SCAN_ENABLED=false** : aucun scan demandé par ce cron avant activation. Aucun secret Worker n’est encore configuré. Le webhook Telegram n’a pas été enregistré par cette tâche.

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

**Après validation du fonctionnement Cloudflare**, retirer uniquement les blocs `on.schedule` de `.github/workflows/scan.yml` et `.github/workflows/telegram-commands.yml`. Conserver `workflow_dispatch`, les déclenchements de publication des favoris, les permissions et le groupe `uniqlo-monitor`. Ne pas désactiver les workflows entiers. Important : modifier scan.yml est lui-même un déclencheur de scan au push ; pour cette seule migration sans scan de test, utiliser un commit avec `[skip actions]`, après tests locaux, puis vérifier les deux workflows conservés. Aucun calendrier n’a été retiré lors du déploiement initial inactif.

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
