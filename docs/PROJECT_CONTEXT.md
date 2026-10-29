# Contexte de référence — UNIQLO Alert

Mis à jour le **29 octobre 2026, Europe/Paris**. Ce document décrit l’état courant ; les anciens états sont dans [HISTORY.md](HISTORY.md). Le code et les vérifications datées priment sur les souvenirs de conversation. Une configuration personnelle peut évoluer : la revérifier avant toute conclusion.

## Objectif et périmètre

Extension Chrome personnelle et gratuite pour les **favoris UNIQLO France, EUR**, avec lecture des prix sur GitHub Actions, même PC éteint. Dépôt : [werti4/uniqlo-alert](https://github.com/werti4/uniqlo-alert), branche de code `main`.

- Petite fenêtre automatique sur `www.uniqlo.com`, réductible, et popup depuis l’icône Chrome.
- Ajout/retrait en un clic de l’article ouvert, sur une fiche France ; aperçu favoris/baisses/alertes et accès au tableau de bord complet.
- 50 favoris maximum. Les changements sont locaux jusqu’à **Publier les favoris**. Pas de publication automatique implicite.
- GitHub Actions demande un scan toutes les **5 minutes** (`2-57/5 * * * *`), ainsi qu’après publication des favoris. Retards et omissions possibles ; aucun temps réel garanti. À la dernière vérification, aucun lancement `schedule` observé (voir diagnostic ci-dessous).
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
6. **Telegram, après configuration** : file persistée avant envoi, réessais bornés ; activation explicite requise.

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

- Checkout existant `/workspace/uniqlo-alert`, Python 3.12, Node.js >=22, `.venv`, `cryptography==46.0.3`. Pas de dépendance npm d’exécution.
- HTTPS Git avec l’authentification de plateforme : lecture et push vers ce dépôt ont fonctionné. L’API GitHub via `gh` a renvoyé `Forbidden` dans ce cloud ; les droits/API/réseaux doivent être diagnostiqués par opération.
- Aucun contrôle du **Chrome personnel** de l’utilisateur disponible dans cette conversation. L’autorisation de l’utilisateur ne crée pas cette capacité. Ne pas prétendre lire sa clé ou agir dans sa session.
- Le Chromium cloud interdit le chargement réel d’extensions décompressées par politique administrateur. Le test navigateur utilise des pages simulées avec la CSP exacte et les API Chrome simulées.
- Le dernier accès direct à UNIQLO était bloqué par le proxy cloud (CONNECT 403), avant réponse du site. `www.uniqlo.com` a été ajouté au **brouillon** réseau ; sauvegarde/publication/application à revérifier. Cela concerne l’environnement cloud, pas le réseau des runners Actions.
- Les processus ne survivent pas forcément à une nouvelle tâche. Aucun serveur permanent nécessaire au développement local.

## Prochain travail utile

1. Pour une modification : lire [DEVELOPMENT.md](DEVELOPMENT.md), inspecter les fichiers concernés et appliquer uniquement le périmètre demandé.
2. Pour valider le fonctionnement personnel : actualiser les données GitHub dans l’extension, vérifier au moins un prix valide, sa date et les erreurs éventuelles. Relever les compteurs du scan si disponibles, sans afficher les favoris en clair.
3. Confirmer le rendu corrigé dans le Chrome utilisateur ; ne pas lui faire recréer un jeton ou une clé si la connexion fonctionne déjà.
4. Examiner les mentions réelles de promotion lorsque l’accès le permet. Les cas synthétiques actuels ne valident pas les offres membres/temporaires.
5. `UA_TELEGRAM_ENABLED=true` est confirmé dans le scan 40804764809, exécuté avec succès. Constater la livraison d’une véritable alerte lorsqu’une baisse ou une alerte en attente existe. Le message de test est déjà reçu : ne pas recréer le bot, ses secrets ou la clé de chiffrement.

Guides complémentaires : [installation et configuration](SETUP.md), [preuves et limites de validation](VALIDATION.md), [historique archivé](HISTORY.md).

## Test de liaison Telegram

Le bot a été créé et les deux secrets ont permis un test réel réussi. Le workflow manuel `.github/workflows/test-telegram.yml` vérifie getMe et getChat privé, puis envoie un seul message de test via `tools/telegram_check.py`. Aucune lecture de favori, aucune clé de chiffrement, aucune modification d’historique ; aucune exécution automatique au push ou sur calendrier. Les erreurs ne divulguent ni URL contenant le jeton, ni réponse API personnelle. Test possible avant l’activation des alertes normales. L’activation normale pourra ensuite livrer les anciennes alertes encore en attente.

Validation locale de la préparation : 32 tests Python (dont 5 tests du diagnostic) et 19 tests JavaScript réussis, avec réseau Telegram simulé. Depuis, un test réel a été effectué : **Tester Telegram 40804020828**, succès, et réception explicitement confirmée par l’utilisateur le 29 octobre 2026. Le message est identifié comme test, sans baisse de prix. La prise en compte de `UA_TELEGRAM_ENABLED=true` a depuis été confirmée dans le scan 40804764809, avec l’étape « Vérifier la configuration — Telegram activé » et le scan tous deux réussis. Ne pas recréer la clé de chiffrement ni le jeton GitHub existants.

Diagnostic publié sur `main` au commit `3389583`. [CI 40802430270 réussie](https://github.com/werti4/uniqlo-alert/actions/runs/40802430270), incluant les 32 tests Python, 19 tests JS, le contrôle navigateur et le paquet. Le workflow manuel [Tester Telegram](https://github.com/werti4/uniqlo-alert/actions/workflows/test-telegram.yml) est disponible ; il a maintenant été lancé avec succès avec les secrets réels. Ne pas confondre ce test manuel avec la livraison automatique d’une alerte de baisse.

Activation automatique vérifiée le 29 octobre 2026 : [scan 40804764809](https://github.com/werti4/uniqlo-alert/actions/runs/40804764809) avec statut explicite « Telegram activé », étape scanner et résumé réussis. Le workflow affiche désormais ce statut résolu depuis la variable Actions et indique dans son résumé si les identifiants sont présents. Aucun changement de prix fictif ni nouvelle clé créés. La première livraison d’une véritable alerte reste à constater ; les compteurs privés du scan ne sont pas accessibles à l’agent.

## Déclenchements planifiés non observés

Après la capture utilisateur montrant uniquement des commits et lancements manuels, vérification directe de GitHub : workflow existant et actif (`workflowActive: true`), dépôt non forké, branche par défaut `main`, cron `2-57/5 * * * *` bien publié sur cette branche. L’historique public complet affichait **7 exécutions**, toutes par push ou lancement manuel, aucune par `schedule`. Dernier scan visible : `40805039423`, push de favoris `b96abed`, le 29 octobre à 02:13:06 UTC (03:13:06 Paris).

La réussite des scans déclenchés par push/manuellement et l’activation Telegram ne prouvent donc pas que le calendrier s’exécute. Cause non établie ; la documentation GitHub autorise retards/omissions, mais ce n’est pas une explication vérifiée pour ce dépôt. Ne pas annoncer une cadence automatique opérationnelle avant un lancement planifié réel. Le cron valide n’a pas été modifié sans diagnostic.

## Commande Telegram `/logs`

Demande utilisateur : récupérer les informations de diagnostic depuis Telegram. Implémentation `tools/telegram_commands.py`, workflow indépendant `.github/workflows/telegram-commands.yml` (schedule `4-59/5`, workflow_dispatch disponible mais non lancé par l’agent). Aucun changement du scanner, de son workflow ou de sa cadence ; aucun déclenchement de scan au push de cette fonctionnalité.

Commande privée `/logs` ou `/logs@NomDuBot` : résumé de l’état chiffré et cinq derniers runs du scanner, pas de téléchargement des logs bruts. Autorisation par type private + chat ID + expéditeur, sans secret dans les réponses ou erreurs. Curseur chiffré séparé `data/telegram-commands.enc.json` sur monitor-data ; aucune écriture dans state.enc.json. Lecteur désormais sérialisé avec le scanner via le groupe uniqlo-monitor ; réponses bornées à trois par passage, curseur sauvegardé après envoi confirmé, mise en lot des messages ignorés. Le bot reçoit les commandes seulement quand le workflow tourne : retards GitHub et absence de schedule déjà constatée restent des limitations explicites. Pas de réponse instantanée ni d’hébergement permanent promis.

Validation locale : 40 tests Python, 19 tests JavaScript réussis. Huit nouveaux tests : autorisation, suffixe bot, réessai après échec, curseur, bornes, confidentialité du rapport et des erreurs, données absentes et signalement de l’absence de schedule. Aucun message réel, aucun scan forcé. Réponse réelle à /logs et exécution planifiée du lecteur restent à vérifier.

Commande /logs publiée au commit `43eaf3c`. [CI 40806326643 réussie](https://github.com/werti4/uniqlo-alert/actions/runs/40806326643), suites Python/JS et contrôle navigateur inclus. Le workflow **Commandes Telegram** est déclaré actif ; aucune exécution de ce nouveau lecteur n’était visible lors de la vérification de publication. Aucun scan ni workflow manuel n’a été déclenché. La réponse réelle à /logs reste à constater lors d’un passage planifié.

## Commande privée `/scan` demandée par l’utilisateur

L’utilisateur autorise maintenant explicitement un scan déclenché par sa commande Telegram /scan, avec messages de début, de fin et bilan des promotions. Sa précédente consigne de ne pas forcer de lancement reste appliquée aux essais de l’agent : aucun workflow manuel ni scan réel déclenché pour développer ce changement. Aucun chemin déclenchant le scanner au push n’est modifié.

Implémentation `tools/telegram_scan.py`, appelée par le lecteur après authentification de la conversation privée et consommation persistée de la demande. Un scan maximum par passage ; requête consommée avant lancement pour éviter sa répétition en cas de panne de réponse. Les fonctions du scanner existant sont réutilisées sans toucher à scanner/monitor.py : déchiffrement/validation, robots.txt, scan borné, sauvegarde chiffrée inconditionnelle du relevé, puis livraison des alertes en attente. Le groupe de concurrence du lecteur devient uniqlo-monitor, commun au scanner ; durée maximum 12 minutes.

Le bilan privé inclut tous les favoris actifs publiés fraîchement vérifiés dont le prix est inférieur au prix de base, y compris les promotions déjà présentes avant l’ajout. Seuls les prix valides de ce passage sont listés. « Aucun article en promo » exige une vérification complète avec prix de base disponible ; les résultats partiels sont annoncés. Aucun changement de la règle de première observation sans alerte automatique. /logs reste en lecture seule et ajoute le lien de l’exécution du dernier état, y compris un /scan exécuté par le lecteur.

Validation locale : 47 tests Python et 19 tests JavaScript réussis, API et collecte simulées. Nouveaux cas : autorisation/consommation, unicité par passage, message initial échoué sans replay, promotions existantes, absence de promo complète vs erreurs/données anciennes/base absente, favoris pausés, réutilisation du moteur, sauvegarde et réponses sans secrets. Réponse réelle à /scan et collecte complète non vérifiées ; la limitation du scheduler reste explicite.

Commande /scan publiée au commit `fe3cc9f`, [CI 40841802154 réussie](https://github.com/werti4/uniqlo-alert/actions/runs/40841802154), 47 tests Python, 19 tests JS et contrôle navigateur inclus. Aucun scan réel ni workflow de commandes déclenché par l’agent. Les messages de progression et le bilan réel restent à constater après une commande utilisateur prise en charge par Actions.
