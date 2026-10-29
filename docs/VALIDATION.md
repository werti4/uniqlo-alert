# Validation actuelle et preuves

État consolidé le 29 octobre 2026 (Europe/Paris). Les anciennes validations et leurs limites initiales sont conservées dans [HISTORY.md](HISTORY.md). Ce document ne constitue pas une nouvelle exécution des tests.

## Code publié 1.1.2

| Contrôle | Preuve disponible | Limite |
| --- | --- | --- |
| Tests Python | 32 réussis localement et en CI après ajout du diagnostic Telegram | Fixtures synthétiques, pas une preuve de collecte réelle |
| Tests JavaScript | 19 réussis localement ; CI réussie | Incluent chiffrement Python/JS, concurrence et protection des données |
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
