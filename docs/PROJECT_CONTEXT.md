# Contexte de référence — UNIQLO Alert

État consolidé le **29 octobre 2026, Europe/Paris**, depuis `main` après la migration `5fdd32a`. Ce fichier décrit les décisions et la configuration courantes. [CODEX_HANDOFF.md](CODEX_HANDOFF.md) donne la reprise courte, [VALIDATION.md](VALIDATION.md) les preuves datées et [HISTORY.md](HISTORY.md) les anciens états.

## Situation actuelle

**Configuration Cloudflare/Telegram terminée.** Webhook confirmé, commandes traitées automatiquement par Actions, premier scan horaire naturel réussi à **13:17 Paris (12:17 UTC)**. Les deux anciens calendriers GitHub ont ensuite été retirés. L’utilisateur indique que tout semble bien fonctionner ; deux autres runs de commandes ont réussi à 13:28 et 13:34 Paris. Aucune saisie de secret ni activation restante identifiée.

Worker : **[uniqlo-telegram-webhook](https://uniqlo-telegram-webhook.uniqlo-alert-werti4.workers.dev)**. Cron Cloudflare actif : `17 * * * *` (UTC ; minute 17 également à Paris). `HOURLY_SCAN_ENABLED=true`, `HOURLY_VERIFY_ENABLED=false`, `SETUP_ENABLED=false` dans le déploiement vérifié et les sources. Les anciens échecs de format du secret sont résolus : ne recréer ni Worker ni secrets.

Toutes les commandes Telegram actuelles et futures passent par Cloudflare. **Catalogue unique `telegram-webhook/commands.json` + routage Cloudflare + traitement + tests + documentation + déploiement Worker sont obligatoires.** Un commit GitHub ne déploie pas le Worker ; aucun pipeline de déploiement Cloudflare automatique n’est installé. Contrat : [TELEGRAM_COMMANDS.md](TELEGRAM_COMMANDS.md).

## Objectif et périmètre

Extension Chrome personnelle et gratuite pour les **favoris UNIQLO France, EUR**, avec lecture des prix sur GitHub Actions, même PC éteint. Dépôt : [werti4/uniqlo-alert](https://github.com/werti4/uniqlo-alert), branche de code `main`.

- Petite fenêtre automatique sur `www.uniqlo.com`, réductible, et popup depuis l’icône Chrome.
- Ajout/retrait en un clic de l’article ouvert, sur une fiche France ; aperçu favoris/baisses/alertes et accès au tableau de bord complet.
- 50 favoris maximum. Les changements sont locaux jusqu’à **Publier les favoris**. Pas de publication automatique implicite.
- Objectif actuel : Cloudflare demande **un scan par heure**, plus `/scan` Telegram à la demande. Worker et webhook actifs, accès validés, horaire naturel confirmé à 13:17 Paris. Les anciens calendriers GitHub sont retirés après cette preuve.
- **Test Telegram reçu par l’utilisateur** ; notifications automatiques facultatives, activation `UA_TELEGRAM_ENABLED=true` confirmée par GitHub dans le scan 40804764809. Ne pas les demander comme préalable aux relevés.
- Hors périmètre actuel : tout le catalogue, achat automatique, connexion UNIQLO, hébergement payant, contournement de protections, autres projets personnels.

## État vérifié et limites

| Élément | Dernière preuve | Portée exacte |
| --- | --- | --- |
| Code publié | Extension **1.1.2** sur `main`, configuration horaire validée dans `5fdd32a` | Le manifeste du dépôt fait foi ; la version installée chez l’utilisateur peut être différente |
| Installation Chrome | Capture utilisateur de 1.1.0 | Installation observée avec styles cassés ; rendu du correctif chez l’utilisateur non confirmé |
| Correctif d’affichage | 1.1.1, commit `10daff5` ; test repris dans 1.1.2 | CSS compatible CSP, largeur 360 px, vérifiés sur pages simulées |
| CI du code 1.1.2 | [40799781846](https://github.com/werti4/uniqlo-alert/actions/runs/40799781846), succès | Tests Python/JS, test navigateur, icônes et artefact |
| Favoris publiés | `data/watchlist.enc.json` ajouté par `5c97080` sur `main` | Favoris chiffrés présents ; contenu personnel non déchiffré par l’agent |
| Historique distant | Branche `monitor-data`, fichier `data/state.enc.json` | État chiffré mis à jour par les scans ; ne pas figer sa révision ni le fusionner dans main |
| Exécution scanner | [40872057387](https://github.com/werti4/uniqlo-alert/actions/runs/40872057387), premier déclenchement horaire naturel du 29/10/2026 à 13:17 Paris | Étape scanner réellement exécutée avec succès ; ne prouve pas une lecture complète de chaque article |
| Prix réels dans Chrome | Non constatés par l’agent | Vérifier prix, date de lecture et erreurs par article après actualisation de l’extension |
| Telegram / iPhone | Test [40804020828](https://github.com/werti4/uniqlo-alert/actions/runs/40804020828) réussi ; utilisateur confirme avoir reçu le message | Liaison et activation automatique confirmées ; scan 40804764809 réussi, livraison d’une véritable alerte de prix encore à constater |
| Promotions du site actuel | Lecture directe bloquée par le réseau cloud lors du dernier essai | Offres temporaires, prix membres et dates restent à examiner sur des fiches réelles |

Un workflow vert ne prouve pas une lecture complète de chaque article ni une notification reçue. Les anciens scans ignorés et blocages sont archivés dans [HISTORY.md](HISTORY.md), sans action de configuration à répéter.

## Architecture et circulation des données

1. **Chrome** : favoris, réglages, clé et jeton dans `chrome.storage.local`, accès réservé aux contextes de confiance.
2. **Publication explicite** : `background.js` chiffre les favoris en AES-256-GCM et écrit `main:data/watchlist.enc.json`. Les conflits de révision préservent les changements locaux.
3. **Actions** : `scan.yml` transmet la clé Actions et le `GITHUB_TOKEN` automatique à `scanner/monitor.py`. Aucun PAT de l’utilisateur nécessaire dans Actions.
4. **Scanner** : déchiffre, lit les fiches autorisées progressivement, conserve les prix valides et écrit l’état chiffré dans `monitor-data:data/state.enc.json`.
5. **Actualisation Chrome** : lit/déchiffre les relevés GitHub. Le rafraîchissement local de la petite fenêtre ne lance pas de scan UNIQLO et ne remplace pas une synchronisation GitHub.
6. **Cloudflare** : webhook `/telegram`, secret officiel Telegram et accès privé au propriétaire, catalogue unique, file persistée avant accusé, puis dispatch automatique de `telegram-commands.yml`. Actions lit `/pending`, exécute la commande puis confirme `/ack`. Résultat final soumis au délai du runner.
7. **Calendrier Cloudflare** : `17 * * * *` enregistré ; `HOURLY_SCAN_ENABLED=true` active le dispatch de `scan.yml` après validation des accès. Après activation, 24 demandes/jour, sans garantie de 24 démarrages immédiats ou scans réussis.

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

## Configuration Cloudflare et Actions déployée

| Élément | Configuration validée le 29/10/2026 |
| --- | --- |
| Compte Cloudflare | `6f5af3971fa548918e6b51e78c26a4c1` |
| Worker / URL | `uniqlo-telegram-webhook` / https://uniqlo-telegram-webhook.uniqlo-alert-werti4.workers.dev |
| Webhook Telegram | URL racine + `/telegram`, secret officiel, `allowed_updates=["message"]`, `max_connections=1`, updates conservées |
| Durable Object | `INBOX` → `TelegramInbox`, SQLite, migration `v1`, namespace `84ca5eaff5764f178aa74c2854fd70be` |
| Variables Worker | `GITHUB_REPOSITORY=werti4/uniqlo-alert`, `GITHUB_BRANCH=main`, `HOURLY_SCAN_ENABLED=true`, `HOURLY_VERIFY_ENABLED=false`, `SETUP_ENABLED=false` |
| Secrets Worker requis | `WEBHOOK_SECRET`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `BOT_USERNAME`, `GITHUB_DISPATCH_TOKEN` ; présents, contrôles d’identité/concordance et dispatch réussis sans lecture des valeurs |
| Secret Worker supplémentaire | `UA_TELEGRAM_WEBHOOK_SECRET`, inutilisé ; laissé intact, distinct du nom attendu `WEBHOOK_SECRET` |
| Variables Actions | `UA_TELEGRAM_WEBHOOK_URL` = URL racine sans `/telegram`, `UA_TELEGRAM_ENABLED=true` |
| Secrets Actions | `UA_TELEGRAM_WEBHOOK_SECRET` = même valeur que `WEBHOOK_SECRET` ; `TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID` concordants ; `UA_ENCRYPTION_KEY` conservée |
| Exécution Actions | `scan.yml` et `telegram-commands.yml` actifs par `workflow_dispatch`, sans `on.schedule` ; déclencheurs de publication de favoris conservés, groupe `uniqlo-monitor`, annulation désactivée |
| Administration | `configure-cloudflare.yml` manuel, `verify_only=true` par défaut ; `/configure` fermé, `/configuration-status` authentifié et en lecture seule |

La file durable conserve jusqu’à 20 commandes, en traite trois par passage (un scan maximum), déduplique les updates et retente un dispatch non vidé après dix minutes. Avec l’URL Actions renseignée, le lecteur utilise `/pending` et `/ack`, **jamais getUpdates en parallèle du webhook**. Les acquittements et résultats restent soumis aux limites des API ; une interruption juste après un envoi peut produire un doublon.

Les valeurs secrètes n’ont pas été lues ni publiées. Le PAT Worker a réussi les accès et dispatchs nécessaires ; cela ne constitue pas une inspection exhaustive de tous ses droits. `UA_ENCRYPTION_KEY` reste exclusivement dans Chrome/Actions, jamais dans Cloudflare.

## Commandes disponibles

- `/logs` : diagnostic et cinq derniers runs du scanner, sans scan ni logs bruts personnels.
- `/scan` : scan des favoris actifs publiés, progression puis promotions, y compris présentes dès l’ajout. Bilan incomplet explicite si erreurs, articles différés ou prix de référence manquant.
- `/favoris` : tous les favoris publiés, actifs ou pausés, derniers prix datés, 🔴 promotion et prix de référence disponible ; prix absents/anciens et erreurs signalés. **Aucun scan** ; utiliser `/scan` pour actualiser.

Accusé rapide depuis Cloudflare, résultat après le délai du runner Actions. Aucune intervention manuelle dans Actions normalement nécessaire pour ces commandes.

## Limites et points à observer

Aucun blocage de configuration connu. Le succès horaire prouve le chemin Cloudflare → Actions et l’exécution du scanner ; il ne garantit ni les prochains horaires, ni chaque lecture UNIQLO, ni une future alerte de prix reçue sur l’iPhone. Consulter les dates/erreurs par article. La confirmation générale de l’utilisateur ne constitue pas un test séparé de chaque commande ou d’une baisse réelle.

Aucune offre payante souscrite. Architecture compatible avec Free et ses [quotas documentés](../telegram-webhook/README.md#quotas-gratuits-et-limites-réelles), sans service illimité. Le connecteur Cloudflare refuse la lecture Billing : le palier exact reste consultable dans le tableau de bord, sans modification d’abonnement. La vérification ponctuelle de 13:25 a été désactivée après validation naturelle ; aucun suivi en arrière-plan supplémentaire promis.

## Reprise, maintenance et retour arrière

1. Lire AGENTS.md, ce contexte, [DEVELOPMENT.md](DEVELOPMENT.md), le contrat des commandes et le guide Worker. Récupérer la dernière `origin/main` avant publication : des changements Chrome peuvent arriver pendant la tâche. Ne pas forcer la branche.
2. Préserver l’extension, la clé et les réglages, `main:data/watchlist.enc.json`, ainsi que l’historique et le curseur chiffrés sur `monitor-data`. Aucun déchiffrement nécessaire pour la maintenance documentaire.
3. Pour un changement applicatif : tests Python/Node et contrôles ciblés, Wrangler dry-run si Worker ; publier et déployer les mêmes sources en conservant secrets, bindings SQLite et switches actifs. Documentation seule : cohérence, liens et `git diff --check`, sans relancer de scan.
4. Vérification administrative depuis iPhone : workflow **Configurer Cloudflare sans scan**, `verify_only=true`. Cette lecture n’envoie ni message ni scan ; ne pas lancer le workflow de commandes pour tester. Les accès disponibles sont à revérifier dans chaque conversation, sans demander de secret dans le chat.
5. Retour arrière : désactiver l’horaire dans les sources et le déploiement ; retirer le webhook sans supprimer les updates, attendre les lecteurs, vider l’URL Actions, puis rétablir un seul calendrier de repli si nécessaire. Conserver le DO et traiter sa file avant basculement, ne jamais régénérer la clé. Procédure : [guide Worker](../telegram-webhook/README.md#mise-à-jour-et-retour-arrière).

Git fetch HTTPS fonctionne dans l’environnement observé ; push direct sans identifiants et `gh` indisponible. Le connecteur GitHub permet publication tree/commit/update_ref avec SHA attendu, sans forcer. Il ne lit/gère pas les secrets/variables Actions ; la validation utilise les runtimes sécurisés. Le connecteur Cloudflare disponible pendant l’activation permet configuration/déploiement, sans accès Billing. Ne pas supposer ces capacités dans une autre conversation.

Le Chrome personnel de l’utilisateur n’est pas contrôlable ici. Le test navigateur utilise le vrai HTML/CSP avec API simulées ; l’installation/rendu sur l’appareil reste une vérification distincte. Le dernier refus proxy cloud sur UNIQLO ne décrit pas le réseau des runners Actions.
