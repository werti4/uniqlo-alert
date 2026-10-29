# Contexte de référence — UNIQLO Alert

Mis à jour le **29 octobre 2026, Europe/Paris**. Ce document décrit l’état courant ; les anciens états sont dans [HISTORY.md](HISTORY.md). Le code et les vérifications datées priment sur les souvenirs de conversation. Une configuration personnelle peut évoluer : la revérifier avant toute conclusion.

## Objectif et périmètre

Extension Chrome personnelle et gratuite pour les **favoris UNIQLO France, EUR**, avec lecture des prix sur GitHub Actions, même PC éteint. Dépôt : [werti4/uniqlo-alert](https://github.com/werti4/uniqlo-alert), branche de code `main`.

- Petite fenêtre automatique sur `www.uniqlo.com`, réductible, et popup depuis l’icône Chrome.
- Ajout/retrait en un clic de l’article ouvert, sur une fiche France ; aperçu favoris/baisses/alertes et accès au tableau de bord complet.
- 50 favoris maximum. Les changements sont locaux jusqu’à **Publier les favoris**. Pas de publication automatique implicite.
- GitHub Actions demande un scan toutes les **5 minutes** (`2-57/5 * * * *`), ainsi qu’après publication des favoris. Retards et omissions possibles ; aucun temps réel garanti.
- **Configuration Telegram demandée par l’utilisateur**, en cours ; notifications toujours facultatives et désactivées tant que l’activation n’est pas effectuée. Ne pas les demander comme préalable aux relevés.
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
| Telegram / iPhone | Configuration maintenant demandée ; bot pas encore créé selon la réponse utilisateur | Aucun envoi ni réception confirmés ; test manuel prêt à être configuré |
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
5. Accompagner maintenant la création du bot dans @BotFather, l’enregistrement des deux secrets, le test manuel **Tester Telegram**, puis l’activation `UA_TELEGRAM_ENABLED=true` après réception vérifiée. Ne pas demander de jeton dans le chat.

Guides complémentaires : [installation et configuration](SETUP.md), [preuves et limites de validation](VALIDATION.md), [historique archivé](HISTORY.md).

## Test de liaison Telegram

L’utilisateur confirme ne pas encore avoir créé de bot. Le workflow manuel `.github/workflows/test-telegram.yml` vérifie getMe et getChat privé, puis envoie un seul message de test via `tools/telegram_check.py`. Aucune lecture de favori, aucune clé de chiffrement, aucune modification d’historique ; aucune exécution automatique au push ou sur calendrier. Les erreurs ne divulguent ni URL contenant le jeton, ni réponse API personnelle. Test possible avant l’activation des alertes normales. L’activation normale pourra ensuite livrer les anciennes alertes encore en attente.

Validation locale de cette préparation : 32 tests Python (dont 5 nouveaux tests du diagnostic) et 19 tests JavaScript réussis. Réseau Telegram simulé pour les tests ; aucun message réel envoyé. Étapes personnelles indispensables : création du bot avec @BotFather, Démarrer dans sa conversation, secrets Actions TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID, lancement manuel du test, réception sur iPhone, puis variable Actions UA_TELEGRAM_ENABLED=true. Ne pas recréer la clé de chiffrement ni le jeton GitHub existants.
