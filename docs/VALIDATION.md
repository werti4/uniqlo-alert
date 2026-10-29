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

Reste à confirmer : variable Actions `UA_TELEGRAM_ENABLED=true`, scan avec Telegram activé, puis livraison d’une véritable alerte de baisse (ou d’une alerte déjà en attente). La réussite du test ne prouve pas que cette activation automatique a été enregistrée. Aucun secret ni identifiant personnel consigné dans ce document.
