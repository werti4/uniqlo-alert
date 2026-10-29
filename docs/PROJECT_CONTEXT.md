# Contexte de référence — UNIQLO Alert

Mis à jour le **29 octobre 2026, Europe/Paris**. Ce document décrit l’état courant ; les anciens états sont dans [HISTORY.md](HISTORY.md). Le code et les vérifications datées priment sur les souvenirs de conversation. Une configuration personnelle peut évoluer : la revérifier avant toute conclusion.

## Décision prioritaire — commandes Telegram dans Cloudflare

**Toutes les commandes Telegram actuelles et futures passent obligatoirement par Cloudflare** pour réception, reconnaissance, autorisation et routage. Catalogue unique : `telegram-webhook/commands.json`, partagé avec l’exécutant. Lire [TELEGRAM_COMMANDS.md](TELEGRAM_COMMANDS.md) avant toute nouvelle commande. Ne jamais ajouter une fonctionnalité uniquement au polling Python ou à un workflow manuel. Le traitement long d’un scan peut rester dans GitHub Actions, déclenché automatiquement par Cloudflare ; la réception et le résultat final ne sont pas la même garantie de délai.

**Premier déploiement Cloudflare effectué le 29 octobre 2026 à 11:20 Paris. Le Worker et le Durable Object SQLite existent, mais les secrets ne sont pas encore fournis : webhook Telegram et scans horaires NON ACTIVÉS.** Après chaque ajout de commande, mise à jour du catalogue + traitement + tests + documentation + redéploiement du Worker requis. Une publication GitHub seule ne suffit pas.

## Objectif et périmètre

Extension Chrome personnelle et gratuite pour les **favoris UNIQLO France, EUR**, avec lecture des prix sur GitHub Actions, même PC éteint. Dépôt : [werti4/uniqlo-alert](https://github.com/werti4/uniqlo-alert), branche de code `main`.

- Petite fenêtre automatique sur `www.uniqlo.com`, réductible, et popup depuis l’icône Chrome.
- Ajout/retrait en un clic de l’article ouvert, sur une fiche France ; aperçu favoris/baisses/alertes et accès au tableau de bord complet.
- 50 favoris maximum. Les changements sont locaux jusqu’à **Publier les favoris**. Pas de publication automatique implicite.
- Objectif actuel : Cloudflare demande **un scan par heure**, plus `/scan` Telegram à la demande. Worker déployé, activation horaire en attente des accès. L’ancien calendrier GitHub de 5 minutes reste publié jusqu’à validation de la bascule ; ne pas le retirer prématurément.
- **Test Telegram reçu par l’utilisateur** ; notifications automatiques facultatives, activation `UA_TELEGRAM_ENABLED=true` confirmée par GitHub dans le scan 40804764809. Ne pas les demander comme préalable aux relevés.
- Hors périmètre actuel : tout le catalogue, achat automatique, connexion UNIQLO, hébergement payant, contournement de protections, autres projets personnels.

## État vérifié et limites

| Élément | Dernière preuve | Portée exacte |
| --- | --- | --- |
| Code publié | Extension **1.1.2**, changement fonctionnel `f9caa99` sur `main` | Le manifeste du dépôt fait foi ; la version installée chez l’utilisateur peut être différente |
| Installation Chrome | Capture utilisateur de 1.1.0 | Installation observée avec styles cassés ; rendu du correctif chez l’utilisateur non confirmé |
| Correctif d’affichage | 1.1.1, commit `10daff5` ; test repris dans 1.1.2 | CSS compatible CSP, largeur 360 px, vérifiés sur pages simulées |
| CI du code 1.1.2 | [40799781846](https://github.com/werti4/uniqlo-alert/actions/runs/40799781846), succès | Tests Python/JS, test navigateur, icônes et artefact |
| Favoris publiés | `data/watchlist.enc.json` ajouté par `5c97080` sur `main` | Favoris chiffrés présents ; contenu personnel non déchiffré par l’agent |
| Historique distant | Branche `monitor-data`, commit observé `5981a24`, fichier `data/state.enc.json` | État chiffré sauvegardé par le scanner |
| Exécution scanner | [40801261438](https://github.com/werti4/uniqlo-alert/actions/runs/40801261438) : contrôle, installation et **Scanner les favoris exécutés avec succès** | Ce ne sont plus des étapes ignorées ; les compteurs de lectures n’ont pas pu être lus publiquement |
| Prix réels dans Chrome | Non constatés par l’agent | Vérifier prix, date de lecture et erreurs par article après actualisation de l’extension |
| Telegram / iPhone | Test [40804020828](https://github.com/werti4/uniqlo-alert/actions/runs/40804020828) réussi ; utilisateur confirme avoir reçu le message | Liaison et activation automatique confirmées ; scan 40804764809 réussi, livraison d’une véritable alerte de prix encore à constater |
| Promotions du site actuel | Lecture directe bloquée par le réseau cloud lors du dernier essai | Offres temporaires, prix membres et dates restent à examiner sur des fiches réelles |

**Ne plus annoncer « aucun favori publié » ou « scan ignoré » sur la base des anciennes exécutions.** Le premier workflow `40799781946` avait ignoré le scan ; l’exécution ultérieure ci-dessus l’a exécuté. À l’inverse, un workflow vert et une branche de données ne prouvent pas combien d’articles ont été lus ni la livraison d’une notification.

## Architecture et circulation des données

1. **Chrome** : favoris, réglages, clé et jeton dans `chrome.storage.local`, accès réservé aux contextes de confiance.
2. **Publication explicite** : `background.js` chiffre les favoris en AES-256-GCM et écrit `main:data/watchlist.enc.json`. Les conflits de révision préservent les changements locaux.
3. **Actions** : `scan.yml` transmet la clé Actions et le `GITHUB_TOKEN` automatique à `scanner/monitor.py`. Aucun PAT de l’utilisateur nécessaire dans Actions.
4. **Scanner** : déchiffre, lit les fiches autorisées progressivement, conserve les prix valides et écrit l’état chiffré dans `monitor-data:data/state.enc.json`.
5. **Actualisation Chrome** : lit/déchiffre les relevés GitHub. Le rafraîchissement local de la petite fenêtre ne lance pas de scan UNIQLO et ne remplace pas une synchronisation GitHub.
6. **Cloudflare** : webhook `/telegram`, secret officiel Telegram et accès privé au propriétaire, catalogue unique, file persistée avant accusé, puis dispatch automatique de `telegram-commands.yml`. Actions lit `/pending`, exécute la commande puis confirme `/ack`. Résultat final soumis au délai du runner.
7. **Calendrier Cloudflare** : `17 * * * *` enregistré ; `HOURLY_SCAN_ENABLED=false` garde le dispatch de `scan.yml` inactif tant que les accès ne sont pas prêts. Après activation, 24 demandes/jour, sans garantie de 24 démarrages immédiats ou scans réussis.

`main` contient le code et la liste chiffrée. `monitor-data` contient les relevés ; ne pas remplacer son historique par une branche de développement ou fusionner ses snapshots dans `main`.

## Règles métier à préserver

- **Promotion affichée** : données `prices.promo` inférieures à `prices.base`, sur la même référence et le même groupe de prix. La couleur rouge ou un intitulé commercial ne suffit pas.
- **Alerte de baisse** : prix inférieur au dernier prix valide observé. Le premier relevé, même promotionnel, sert de référence sans alerte.
- Le compteur/filtre **En baisse** compare actuellement au **premier prix relevé** ; les alertes comparent au **dernier prix valide**. Ne pas confondre ces deux calculs lors d’une modification.
- L’objectif de prix est indicatif ; il ne bloque aucune alerte de baisse.
- Couleur/taille : préférences. Prix et stock par variante non vérifiés ; une erreur ne signifie ni zéro euro ni rupture.
- Réseau, robots.txt, 403/429 : conserver les prix valides, afficher les erreurs, respecter les pauses et `Retry-After`. Aucun contournement.
- Le schéma chiffré est `schema: 1` ; l’enveloppe AES-GCM est partagée par JS et Python avec AAD `uniqlo-alert:v1`. Toute évolution doit rester compatible ou prévoir une migration explicite et testée.

## Configuration et secrets : emplacement exact

| Élément | Emplacement / rôle |
| --- | --- |
| Dépôt / branche | Réglages Chrome : `werti4/uniqlo-alert`, `main` |
| PAT limité au dépôt | Stockage local de l’extension ; Contents et Actions lecture/écriture |
| Clé existante | Chrome et **même valeur** dans le secret Actions `UA_ENCRYPTION_KEY` ; ne pas régénérer après publication |
| `GITHUB_TOKEN` du scanner | Fourni automatiquement par Actions, permission `contents: write` sur le job scanner |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Secrets Actions, facultatifs pour les relevés |
| `UA_TELEGRAM_ENABLED` | Variable Actions ; seule la valeur `true` permet au workflow de transmettre les secrets Telegram |

Aucune valeur de secret dans le dépôt, les logs, le paquet, les captures partagées ou le chat. Ne pas déduire l’absence d’une clé d’un refus de lecture de la liste des secrets. La présence de la configuration a permis l’exécution récente ; son état doit être revérifié si un nouveau problème apparaît.

## Environnement de travail et accès

- Checkout de cette tâche : `/workspace/scratch/6e97d4083c7f/uniqlo-alert`, Python 3.12.14, Node.js 24.22.1. Pas de dépendance npm d’exécution. Les chemins et dépendances de chaque environnement sont à revérifier.
- HTTPS Git : fetch fonctionne ; push direct refusé faute d’identifiants dans ce cloud, `gh` non installé. Publication effectuée via le connecteur GitHub (tree/commit puis mise à jour de main avec SHA attendu), sans forcer ni écraser les favoris concurrents. Diagnostiquer les droits par opération.
- Aucun contrôle du **Chrome personnel** de l’utilisateur disponible dans cette conversation. L’autorisation de l’utilisateur ne crée pas cette capacité. Ne pas prétendre lire sa clé ou agir dans sa session.
- Le Chromium cloud interdit le chargement réel d’extensions décompressées par politique administrateur. Le test navigateur utilise des pages simulées avec la CSP exacte et les API Chrome simulées.
- Le dernier accès direct à UNIQLO était bloqué par le proxy cloud (CONNECT 403), avant réponse du site. `www.uniqlo.com` a été ajouté au **brouillon** réseau ; sauvegarde/publication/application à revérifier. Cela concerne l’environnement cloud, pas le réseau des runners Actions.
- Les processus ne survivent pas forcément à une nouvelle tâche. Aucun serveur permanent nécessaire au développement local.

## Déploiement Cloudflare réellement observé — 29 octobre 2026

| Élément | État vérifié |
| --- | --- |
| Compte | `6f5af3971fa548918e6b51e78c26a4c1`, compte Cloudflare associé à werti4 |
| Worker | `uniqlo-telegram-webhook` |
| URL racine | https://uniqlo-telegram-webhook.uniqlo-alert-werti4.workers.dev |
| Version initiale | `5a4568a5-a171-4e64-8e1d-48fef52924f7`, 100 % du trafic, API Cloudflare |
| Durable Object | binding `INBOX`, classe `TelegramInbox`, migration `v1`, **SQLite confirmé** |
| Namespace | `84ca5eaff5764f178aa74c2854fd70be` |
| Cron enregistré | `17 * * * *` (UTC, minute 17 également à Paris), propagation possible |
| Dispatch horaire | **Désactivé**, `HOURLY_SCAN_ENABLED=false` |
| Variables présentes | `GITHUB_REPOSITORY=werti4/uniqlo-alert`, `GITHUB_BRANCH=main` |
| Secrets Worker | Liste API vide : `WEBHOOK_SECRET`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `BOT_USERNAME`, `GITHUB_DISPATCH_TOKEN` restent à saisir |
| Liaison Actions | `UA_TELEGRAM_WEBHOOK_URL` et `UA_TELEGRAM_WEBHOOK_SECRET` non configurés par cette tâche : connecteur sans capacité de gestion de ces paramètres |
| Webhook Telegram | Pas enregistré par cette tâche ; `getWebhookInfo` réel non accessible sans le jeton renouvelé |
| Accès HTTPS depuis ce cloud | Après propagation et User-Agent applicatif : GET / → 404 JSON ; POST /telegram et /pending sans secret → 403 JSON. Routage public et refus des requêtes non authentifiées confirmés, sans commande ni message |

Le connecteur a permis création du sous-domaine workers.dev, publication du module, migration SQLite, liaison, route workers.dev et cron. La consultation des abonnements est refusée (OAuth sans permission Billing). **Aucun abonnement n’a été créé ou modifié.** Le modèle API `standard` ne prouve pas à lui seul le palier Free ; vérifier Workers Free dans le tableau de bord avant activation. L’architecture est compatible avec Free, selon les quotas documentés dans le guide.

Les secrets GitHub ne sont pas relisibles en clair et aucun outil connecté ne permet ici de créer un PAT personnel limité ni de gérer les variables/secrets Actions. Ne jamais récupérer d’anciens tokens dans les conversations. Saisies masquées et étapes exactes : [guide Cloudflare](../telegram-webhook/README.md). **UA_ENCRYPTION_KEY reste exclusivement dans Actions et Chrome ; ne jamais la transmettre au Worker.** Secrets Telegram existants et favoris conservés.

Dernière vérification GitHub : scan `40840801906`, 29/10/2026 09:15 Paris, réussi, étape « Telegram activé » réussie. C’est une preuve de `UA_TELEGRAM_ENABLED=true` lors de ce run, pas une lecture de la configuration courante ni une validation du nouveau webhook. Les 33 runs consultés ne contenaient aucun lecteur de commandes en cours ; revérifier au moment de la bascule.

## Vérifications de cette tâche et activation restante

- 63 tests Python et 27 tests Node réussis, services simulés ; Wrangler 4.155.0 `deploy --dry-run` réussi, bundle environ 8,15 Kio. L’accusé Telegram est maintenant envoyé avant l’appel de dispatch GitHub ; une panne de dispatch conserve la commande et ne répète pas l’accusé déjà confirmé.
- Script local : `--check` vérifie getWebhookInfo en lecture seule, erreurs masquées ; `/logs` distingue les dispatchs Cloudflare/manuels des schedules GitHub sans inventer leur origine.
- HTTP : User-Agent Python par défaut refusé par Cloudflare 1010 ; en-tête `UniqloAlertBridge/1.0` ajouté au bridge Actions et au script local selon la documentation officielle. Routes publiques et contrôle d’accès vérifiés sans secret.
- API : Worker déployé à 100 %, binding SQLite, migration, variables, cron et domaine vérifiés ; secrets absents explicitement constatés.
- Aucun scan réel, aucun message de test Telegram, aucune lecture/déchiffrement de favoris, aucune modification d’extension ou de clé effectués.
- Reste : vérifier le palier Free, saisir les cinq secrets Worker, configurer les deux paramètres de liaison Actions et vérifier `UA_TELEGRAM_ENABLED=true`, attendre la fin de l’ancien getUpdates, enregistrer puis contrôler le webhook. Activer ensuite `HOURLY_SCAN_ENABLED=true` et conserver cette valeur dans wrangler.jsonc avant les prochains déploiements.
- À confirmer après activation : `/pending` authentifié, URL/allowed_updates/absence d’erreur via getWebhookInfo, commande réelle demandée par l’utilisateur, puis premier Scheduled naturel et run Actions correspondant. Ne pas forcer de scan pour vérifier.
- **Migration des calendriers en attente** : après validation Cloudflare, retirer les blocs `on.schedule` de `scan.yml` et `telegram-commands.yml`, conserver `workflow_dispatch` et les déclenchements de favoris. Modifier scan.yml déclenche actuellement un scan au push : publier cette migration avec `[skip actions]` pour respecter l’absence de scan de test, puis vérifier les déclencheurs conservés. Ne pas désactiver les workflows entiers.

## Commandes et mises à jour obligatoires

- `/logs` : diagnostic et cinq derniers runs du scanner, lecture seule.
- `/scan` : demande un scan des favoris actifs publiés, annonce le début puis le bilan ; promotions présentes dès l’ajout incluses. Résultat incomplet explicite si erreurs/différés/base absente.
- `/favoris` : tous les favoris publiés, actifs et pausés, derniers prix datés, 🔴 promotion et prix de référence disponible ; prix manquants/anciens/erreurs signalés. **Aucun scan.** Utiliser `/scan` pour actualiser.

Une future commande exige **catalogue `commands.json` + routage Cloudflare + traitement + tests + documentation + déploiement du Worker**. Une commande uniquement ajoutée à GitHub est incomplète. Aucun pipeline automatique de déploiement Cloudflare n’est installé.

Mise à jour : récupérer `origin/main` (publications Chrome possibles), conserver les données chiffrées et `monitor-data`, tester Python/Node et Wrangler dry-run, publier en fast-forward, déployer depuis les mêmes sources, conserver les secrets et la valeur réelle du switch horaire. Voir le guide pour les commandes détaillées.

Retour arrière : désactiver le switch horaire, retirer le webhook sans supprimer les messages en attente, attendre la fin des lecteurs webhook, vider la variable Actions d’URL et rétablir un seul calendrier GitHub si nécessaire. Le code polling reste un fallback, jamais simultané au webhook. Ne pas supprimer le Durable Object ni sa file ; ne pas régénérer la clé des favoris.

Publication initiale `ac89367` : [CI 40857882653](https://github.com/werti4/uniqlo-alert/actions/runs/40857882653) entièrement réussie, tests Python/Node, popup CSP, icônes et paquet. Le correctif User-Agent ultérieur est couvert par les 63 tests Python locaux et une CI distincte.
