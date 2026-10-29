# Validation actuelle et preuves

## Dernier contrôle après « C’est corrigé » — 29 octobre 2026, 12:58 Paris

La relance de 40867953571 a encore trouvé un format invalide. Pour écarter un ancien état de run, une exécution **neuve** [40869512253](https://github.com/werti4/uniqlo-alert/actions/runs/40869512253), code `197bbcb`, a été lancée avec un diagnostic limité à des catégories, sans afficher longueur, contenu ou caractère du secret. Résultat exact : **secret Actions UA_TELEGRAM_WEBHOOK_SECRET : caractères non autorisés**. Le contrôle est arrêté avant tout appel HTTP Worker/Telegram, setWebhook non exécuté. Ne plus relancer tant que cette saisie n’est pas corrigée dans GitHub ; ne pas assouplir le format pour contourner le problème.

Intervention iPhone : GitHub Settings → Secrets and variables → Actions → Secrets → **UA_TELEGRAM_WEBHOOK_SECRET** → crayon → saisir un code aléatoire de 64 lettres/chiffres uniquement, sans guillemets, espace, ponctuation ou retour à la ligne → Update secret. Cloudflare **WEBHOOK_SECRET** doit contenir exactement la même valeur. Ce n’est pas TELEGRAM_BOT_TOKEN et ce n’est pas le secret supplémentaire UA_TELEGRAM_WEBHOOK_SECRET dans Cloudflare. Ne communiquer aucune valeur en chat. Si l’utilisateur a seulement changé Cloudflare, il reste impérativement la saisie GitHub.

SETUP_ENABLED a été refermé à false après l’essai ; HOURLY_SCAN_ENABLED et HOURLY_VERIFY_ENABLED restent false, les six noms de secrets sont conservés. Aucun scan forcé, aucun message de test, aucun ancien calendrier retiré. Pas de contrôle horaire naturel planifié tant que l’activation n’a pas réussi. Après correction, rouvrir temporairement l’activation avec une échéance future et utiliser une exécution fraîche du seul workflow de configuration. Le déclencheur push temporaire de diagnostic est retiré après l’essai ; garder workflow_dispatch par défaut en lecture seule.

Tests du diagnostic : 68 Python et 33 Node réussis, dont un test vérifiant les trois catégories de format sans divulgation. Aucun changement du Worker, du scanner, de l’extension, des favoris ni de la clé AES dans cette relance ; seuls la procédure Actions, son diagnostic et le contexte ont évolué.

## État courant — activation iPhone bloquée par le format du secret GitHub

Le 29 octobre 2026, reprise avec connecteur Cloudflare disponible (le blocage d’accès d’une autre conversation ne s’applique pas ici). Worker existant mis à jour sans recréer de ressources ni secrets. Version de code de configuration `8ee90bcf-d183-4ae2-ac30-2d8c577d4686`, migration v1/INBOX et les six noms de secrets conservés (cinq requis + extra inutilisé).

Preuve réelle : workflow dédié [Configurer Cloudflare 40867953571](https://github.com/werti4/uniqlo-alert/actions/runs/40867953571), commit `49265e7`, échec contrôlé **avant tout appel au Worker/Telegram** : `UA_TELEGRAM_WEBHOOK_SECRET` dans Actions est présent mais ne respecte pas le format 32–256 caractères parmi A–Z/a–z/0–9/_/-. Aucun caractère, longueur ou contenu du secret n’a été affiché. Il faut corriger cette saisie, pas relancer aveuglément ni assouplir la validation.

Cette exécution prouve aussi : variable Actions UA_TELEGRAM_WEBHOOK_URL égale à l’URL racine attendue, UA_TELEGRAM_ENABLED=true, secrets Actions TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID non vides (validité et égalité avec Cloudflare NON vérifiées). PAT Worker, identité Telegram, secret partagé, webhook et file authentifiée restent non validés. Aucun setWebhook exécuté par cet essai, aucun scan ni message de test. Aucun prochain scan horaire naturel à vérifier tant que l’horaire reste désactivé.

Après l’essai : **SETUP_ENABLED=false**, **HOURLY_SCAN_ENABLED=false**, **HOURLY_VERIFY_ENABLED=false** confirmés par API. Cron 17 * * * * et anciens calendriers GitHub conservés. Tous les secrets ont été conservés par bindings inherit, puis leur présence a été relue par API. Aucun abonnement modifié. L’endpoint /configure nécessite maintenant une réouverture temporaire explicite et une échéance future pour reprendre ; /configuration-status reste en lecture seule et exige le secret commun. Le déclencheur push initial du workflow de configuration est retiré après cet essai ; workflow_dispatch reste disponible, vérification seule par défaut.

### Intervention utilisateur sur iPhone, sans terminal

1. Dans le gestionnaire de mots de passe, utiliser/générer un code **aléatoire de 64 lettres et chiffres**, sans espace, ponctuation, guillemets ou préfixe. Ce code n’est PAS le jeton BotFather. Ne pas l’envoyer en chat.
2. GitHub → dépôt werti4/uniqlo-alert → Settings → Secrets and variables → Actions → Secrets → crayon sur UA_TELEGRAM_WEBHOOK_SECRET → remplacer par ce code → Update secret.
3. Cloudflare → Worker uniqlo-telegram-webhook → Settings → Runtime variables and secrets → WEBHOOK_SECRET → Rotate → saisir exactement le même code → Deploy. Ne pas modifier UA_ENCRYPTION_KEY ni les jetons Telegram pour cette correction. Le secret UA_TELEGRAM_WEBHOOK_SECRET supplémentaire côté Cloudflare n’est pas utilisé par le Worker.
4. Revenir dans cette conversation et signaler uniquement que c’est corrigé. L’agent réouvrira temporairement SETUP_ENABLED avec une nouvelle échéance, puis relancera le seul workflow de configuration (jamais Scanner UNIQLO ou Commandes Telegram pour tester). Aucun secret à recopier dans la conversation, aucun terminal requis.

Après succès du contrôle : refermer SETUP_ENABLED, activer HOURLY_SCAN_ENABLED avec le connecteur et dans wrangler.jsonc, activer temporairement HOURLY_VERIFY_ENABLED pour le diagnostic automatique du prochain horaire naturel. Programmer alors une vérification future via Automations si l’heure n’est pas atteinte ; cette vérification ne doit pas forcer un scan. Ne retirer les anciens on.schedule qu’après preuve Scheduled/dispatch naturel + run scanner correspondant ; conserver workflow_dispatch et déclenchements de favoris. Actualiser le contexte à chaque résultat réel.

Code publié `49265e7` : [CI 40867953541](https://github.com/werti4/uniqlo-alert/actions/runs/40867953541) entièrement réussie. Tests : **67 Python, 33 Node**, services simulés, Wrangler 4.155.0 dry-run réussi. Le workflow d’activation échoué ne contredit pas la CI : son échec identifie une configuration personnelle invalide, pas un test applicatif échoué.

État consolidé le 29 octobre 2026 (Europe/Paris). Les anciennes validations et leurs limites initiales sont conservées dans [HISTORY.md](HISTORY.md). Ce document ne constitue pas une nouvelle exécution des tests.

## Contrôle après saisie des secrets — relais Codex du 29 octobre 2026

API Cloudflare consultée sans lecture de valeurs : WEBHOOK_SECRET, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, BOT_USERNAME, GITHUB_DISPATCH_TOKEN tous présents au type secret_text. Secret supplémentaire UA_TELEGRAM_WEBHOOK_SECRET côté Cloudflare, inutilisé par le Worker. GITHUB_REPOSITORY=werti4/uniqlo-alert, GITHUB_BRANCH=main, HOURLY_SCAN_ENABLED=false ; binding INBOX et cron 17 * * * * confirmés.

La présence des noms ne valide ni les valeurs, ni les droits/expiration du PAT, ni l’identité Telegram, ni l’égalité du secret commun avec Actions. Configuration GitHub annoncée faite par l’utilisateur, non vérifiable via le connecteur. Renouvellement du jeton signalé par BotFather, copie effective dans les deux services non confirmée. Aucun webhook enregistré, scan réel ou message de test lancé par l’agent pendant ce relais. getWebhookInfo et file authentifiée restent à contrôler. Voir [CODEX_HANDOFF.md](CODEX_HANDOFF.md).

[CI finale du code 1296f30, 40858332943](https://github.com/werti4/uniqlo-alert/actions/runs/40858332943) réussie, incluant tests Python/Node, popup CSP et paquet. Cette mise à jour est documentaire : contrôle du diff et des liens uniquement, sans nouvelle exécution applicative.

## Premier déploiement Cloudflare — 29 octobre 2026, 11:20 Paris

Worker `uniqlo-telegram-webhook`, URL https://uniqlo-telegram-webhook.uniqlo-alert-werti4.workers.dev, version `5a4568a5-a171-4e64-8e1d-48fef52924f7` déployée à 100 %. API Cloudflare : migration v1, binding INBOX → TelegramInbox, namespace SQLite 84ca5eaff5764f178aa74c2854fd70be, route workers.dev active et cron 17 * * * * confirmés. Variables dépôt/branche présentes ; HOURLY_SCAN_ENABLED=false. Au premier déploiement, liste des secrets Worker vide ; cette observation historique est remplacée par le contrôle de saisie ci-dessous. Aucun abonnement créé/modifié ; lecture de facturation refusée par OAuth, palier Free à contrôler dans le tableau de bord.

63 tests Python et 27 tests JS réussis ; Wrangler 4.155.0 dry-run réussi. Régression couverte : accusé avant dispatch GitHub, conservation de la commande après refus de dispatch et accusé non répété lors du réessai. Les API Telegram/GitHub sont simulées. Aucun scan ni message réel déclenché par l’agent. Extension, clé et données chiffrées non modifiées.

HTTP depuis ce cloud : après les premiers 503 de propagation, urllib par défaut a reçu 403 / code Cloudflare 1010. La documentation officielle recommande un User-Agent applicatif sur workers.dev : ajout de `UniqloAlertBridge/1.0` au bridge et au script local, couvert par les tests. Avec cet en-tête : GET / → 404 JSON, POST /telegram et /pending sans secret → 403 JSON. Routage HTTPS et refus non authentifiés confirmés sans commande. File authentifiée à confirmer après saisie des secrets. Aucun getWebhookInfo réel sans jeton actuel disponible ; ni webhook, ni commande réelle, ni dispatch horaire naturel validés. Calendriers GitHub conservés jusqu’à validation de la bascule. Le [guide Cloudflare](../telegram-webhook/README.md) donne les manipulations masquées restantes et le retour arrière.

Publication initiale ac89367 : [CI 40857882653](https://github.com/werti4/uniqlo-alert/actions/runs/40857882653) entièrement réussie (dont popup CSP et paquet). Correctif User-Agent ultérieur : 63 Python / 27 Node réussis localement, CI distincte.

GitHub consulté en lecture seule : dernier scanner 40840801906 réussi à 09:15 Paris, étape « Telegram activé » réussie ; ne prouve pas la valeur actuelle ni la liaison Cloudflare. Aucun lecteur de commandes actif dans les 33 runs consultés. Les entrées de préparation plus bas sont historiques et ne remplacent pas cet état.

## Code publié 1.1.2

| Contrôle | Preuve disponible | Limite |
| --- | --- | --- |
| Tests Python | 63 réussis localement le 29/10 après premier déploiement Cloudflare | Fixtures synthétiques, pas une preuve de collecte réelle |
| Tests JavaScript | 27 réussis localement et dans le job CI du catalogue Cloudflare | Incluent chiffrement Python/JS, concurrence et protection des données |
| Popup sous CSP | Test `tools/check_quick_ui.cjs` réussi localement et en CI | Vrai HTML et CSP, API Chrome simulées ; installation réelle interdite dans le cloud |
| Régression détectée | Le test échoue sur une copie de 1.1.0, réussit sur le correctif | Le défaut historique venait du CSS inline bloqué |
| Paquet | Icônes générées et artefact publié, 13 fichiers autorisés | Artefact à durée de conservation de 7 jours |
| CI de référence | [40799781846](https://github.com/werti4/uniqlo-alert/actions/runs/40799781846), commit fonctionnel `f9caa99` | Ne prouve pas la mise à jour du Chrome utilisateur |
| Contrôle des prérequis Actions | Quatre combinaisons clé/fichier validées localement, scripts embarqués compilés | Contrôle de présence distinct de la lecture d’un article |

Le défaut visuel signalé sur 1.1.0 est corrigé dans le code depuis 1.1.1. Il reste à confirmer le rendu de la version récente dans le Chrome personnel de l’utilisateur. Les tests précédents sans CSP n’étaient pas suffisants ; conserver le test navigateur sous CSP pour les évolutions de la fenêtre.

## Automatisation : état actualisé

- [Ancienne exécution 40799781946](https://github.com/werti4/uniqlo-alert/actions/runs/40799781946) : contrôle de configuration réussi, scan **ignoré** à ce moment-là.
- Depuis, `main` a reçu les favoris chiffrés dans le commit `5c97080` ; `monitor-data` contient un état chiffré au commit observé `5981a24`.
- [Exécution 40801261438](https://github.com/werti4/uniqlo-alert/actions/runs/40801261438) : contrôle de configuration, installation, étape **Scanner les favoris** et résumé tous **exécutés avec succès**. Observation effectuée pendant la consolidation du contexte.
- Les compteurs de lectures n’ont pas été accessibles depuis les logs publics consultés. L’état personnel n’a pas été déchiffré par l’agent. Une liste vide ou des favoris en pause ne peuvent pas être exclus à partir de la seule réussite du job.
- Confirmation fonctionnelle restante : dans Chrome, actualiser GitHub et constater au moins un prix valide avec une date récente, puis vérifier les erreurs par article. La réception du test Telegram est désormais confirmée (voir ci-dessous) ; la livraison automatique d’une alerte de prix reste distincte.

Le calendrier est `2-57/5 * * * *`, sans ponctualité garantie. L’existence de ce calendrier ne démontre pas que chaque lancement planifié a eu lieu. Consulter les exécutions récentes lors du diagnostic.

## Promotions et accès au site

Le code lit le prix de base et le prix promotionnel du groupe produit exact. Les cas synthétiques « promo inférieure », « prix égaux » et « pas de promo » ont été vérifiés. Une promotion au premier relevé ne crée pas d’alerte de baisse.

La dernière tentative de consultation directe de robots.txt a reçu un CONNECT 403 du proxy cloud. Cela ne démontre pas un refus d’UNIQLO envers le runner GitHub. Le domaine UNIQLO a été ajouté au brouillon réseau ; son application reste à revérifier. Les mentions d’offre temporaire, prix membre et dates ne sont pas validées sur le site actuel.

## Pour les prochaines modifications

Suivre [DEVELOPMENT.md](DEVELOPMENT.md). Consigner le commit testé, les commandes, les résultats, les vérifications réelles/simulées et les étapes non exécutées. Après un changement uniquement documentaire, contrôler les liens et le diff ; ne pas inventer de nouvelle validation applicative.

## Test réel Telegram confirmé

Le workflow manuel **Tester Telegram** a été publié au commit `3389583` ; [CI 40802430270 réussie](https://github.com/werti4/uniqlo-alert/actions/runs/40802430270), avec 32 tests Python et 19 tests JavaScript. Les cinq nouveaux tests Python simulent les API et couvrent envoi confirmé, secrets manquants, refus des groupes/mauvaise identité, confidentialité des erreurs et confirmation incomplète.

Depuis, le bot a été créé et les secrets enregistrés. [Test réel 40804020828](https://github.com/werti4/uniqlo-alert/actions/runs/40804020828) terminé avec succès ; le 29 octobre 2026, l’utilisateur confirme avoir reçu le message « UNIQLO Alert — message de test ». Liaison GitHub Actions → conversation privée Telegram vérifiée, sans accès aux favoris ni modification de l’historique.

Activation maintenant confirmée : [scan 40804764809](https://github.com/werti4/uniqlo-alert/actions/runs/40804764809), étape « Vérifier la configuration — Telegram activé », scanner et résumé réussis. Reste à constater la livraison d’une véritable alerte de baisse (ou d’une alerte déjà en attente). Aucun secret ni identifiant personnel consigné dans ce document.

Modification de diagnostic publiée au commit `9fe139e` : statut Telegram visible dans le nom de l’étape Actions et résumé positif lorsque les identifiants sont présents. Tests locaux : résumé activé/désactivé sans fuite de secrets, 32 tests Python et 19 tests JavaScript réussis. La cadence, les favoris, la clé et les règles de baisse sont inchangés.

[CI 40804764814](https://github.com/werti4/uniqlo-alert/actions/runs/40804764814) réussie pour le commit `9fe139e`, incluant les suites et le contrôle navigateur.

## Limite actuelle : calendrier non démontré

Vérification à la suite de la capture utilisateur : 7 exécutions dans l’historique public de Scanner UNIQLO, toutes par commit ou lancement manuel, aucune par `schedule`. Workflow déclaré actif, défaut `main`, dépôt non forké et cron `2-57/5 * * * *` présent sur `main`. Dernière exécution visible : `40805039423` (publication de favoris). La cadence automatique toutes les cinq minutes reste **non vérifiée**, cause de l’absence de déclenchements planifiés non établie. Les succès précédents valident seulement les déclencheurs et étapes effectivement observés.

## Commande `/logs`

40 tests Python et 19 tests JavaScript réussis localement après ajout de huit tests du lecteur de commandes. API simulées : contrôle de l’expéditeur privé, suffixe de commande, non-retraitement, réessai après échec, limitation/batch, diagnostics sans données personnelles, stockage chiffré séparé et erreurs sans jeton. Aucun appel réel Telegram, aucun scan forcé. Le workflow de commandes est configuré pour des passages différés et dépend du scheduler GitHub dont les lancements restent non démontrés. La réponse réelle à /logs n’est pas encore constatée.

Commande /logs publiée au commit `43eaf3c`. [CI 40806326643 réussie](https://github.com/werti4/uniqlo-alert/actions/runs/40806326643), suites Python/JS et contrôle navigateur inclus. Le workflow **Commandes Telegram** est déclaré actif ; aucune exécution de ce nouveau lecteur n’était visible lors de la vérification de publication. Aucun scan ni workflow manuel n’a été déclenché. La réponse réelle à /logs reste à constater lors d’un passage planifié.

## Commande `/scan`

47 tests Python et 19 tests JavaScript réussis localement ; sept nouveaux tests couvrent la demande privée consommée avant exécution, un seul scan par passage, absence de répétition après échec, promotions dès le premier relevé, données anciennes/erreurs/base absente, favoris pausés, sauvegarde avant bilan et erreurs sans secrets. API et lecture UNIQLO simulées, aucun scan réel ni lancement manuel effectué par l’agent. Le déploiement ne modifie aucun fichier couvert par les filtres de push du scanner. La réponse effective à /scan et le déclenchement planifié du lecteur restent à observer.

Commande /scan publiée au commit `fe3cc9f`, [CI 40841802154 réussie](https://github.com/werti4/uniqlo-alert/actions/runs/40841802154), 47 tests Python, 19 tests JS et contrôle navigateur inclus. Aucun scan réel ni workflow de commandes déclenché par l’agent. Les messages de progression et le bilan réel restent à constater après une commande utilisateur prise en charge par Actions.

## Webhook immédiat — préparation

49 tests Python et 23 tests Node réussis : authentification du header, refus hors propriétaire, filtrage des commandes/suffixes, file persistante, déduplication, conservation après refus de dispatch, reconstruction stricte des commandes côté runner et erreurs sans secrets. Wrangler 4.155.0 deploy --dry-run a assemblé le Worker avec son binding Durable Object. Aucun compte ou secret Cloudflare disponible ; déploiement, enregistrement Telegram et réponse réelle **non effectués**. Aucun scan forcé pendant ces validations.

Préparation webhook publiée (`5c74690`, ajustement de confidentialité `e3d18c8`). [CI 40844189873 réussie](https://github.com/werti4/uniqlo-alert/actions/runs/40844189873), suites Python/JS et contrôle navigateur. Worker assemblé en dry-run mais **non déployé**, webhook Telegram **non enregistré**, réception immédiate **non active**. Les identifiants Cloudflare sont absents et aucun connecteur de déploiement n’est disponible ; il reste la création/connexion du compte, le déploiement et la saisie sécurisée des secrets selon telegram-webhook/README.md.

## Préparation du calendrier horaire Cloudflare

49 tests Python et 26 tests Node réussis localement. Les nouveaux cas vérifient un dispatch scan.yml par heure confirmée, aucun message de routine Telegram, switch désactivé, route horaire HTTP non exposée et absence de validation d’un dispatch refusé. Cron `17 * * * *`, HOURLY_SCAN_ENABLED="false" par défaut. Service non déployé : aucun événement Scheduled Cloudflare ni scan horaire réel validé. Ancien cron GitHub encore publié, doublons possibles s’il reprend après activation de Cloudflare ; migration après validation externe.

[CI 40846436147 réussie](https://github.com/werti4/uniqlo-alert/actions/runs/40846436147), commit `ff9214e`. Assemblage Wrangler --dry-run validé avec le cron horaire et le switch désactivé. Aucun événement horaire réel ni déploiement validé.

## Catalogue Cloudflare de toutes les commandes

51 tests Python et 27 tests Node réussis localement. Nouveau contrôle : chaque nom du catalogue partagé est reconnu par Cloudflare et possède un traitement compatible ; un traitement absent est rejeté. La cible et la procédure des futures commandes sont formalisées dans TELEGRAM_COMMANDS.md et AGENTS.md. Services simulés : aucun déploiement ni commande réelle validés.

Contrat et catalogue des commandes publiés au commit `128fff1`. [Job CI 40853282759](https://github.com/werti4/uniqlo-alert/actions/runs/40853282759) : toutes les étapes, y compris tests et contrôle navigateur, terminées avec succès. Catalogue inclus dans le Worker lors du dry-run Wrangler. Cloudflare reste non déployé : aucun service actif ni réponse réelle supplémentaire annoncés.

## `/favoris`

57 tests Python, 27 tests Node réussis localement. Six nouveaux tests : promotions/prix/date, prix absents et erreurs anciennes sans fuite du texte brut, pagination 50 favoris, différence liste vide/échec de lecture, liste conservée quand les relevés sont inaccessibles, autorisation privée sans scan. Le catalogue partagé inclut la commande et le test Cloudflare couvre automatiquement ce nom et son suffixe de bot. Aucun déploiement Cloudflare ni réponse réelle /favoris vérifiés.

/favoris publié (`f99c27d`), [job CI 40854426246](https://github.com/werti4/uniqlo-alert/actions/runs/40854426246) terminé avec toutes les étapes réussies, 57 tests Python et 27 tests Node. Catalogue inclus dans l’assemblage Wrangler --dry-run réussi. Aucun scan ni déploiement réel effectués ; la commande sera active après configuration Cloudflare et validation d’une réponse privée réelle.
