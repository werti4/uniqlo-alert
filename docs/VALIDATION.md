# Validation de la version initiale fiabilisée

Contrôles locaux effectués le 29 octobre 2026, après intégration des quatre revues.

| Contrôle | Résultat |
| --- | --- |
| Tests Python scanner | 27 réussis |
| Tests JavaScript extension et intégration | 17 réussis, dont 2 échanges chiffrés Chrome/Python |
| Dépendance testée | `cryptography==46.0.3`, identique à `requirements.txt` |
| Lecture d'une fiche publique capturée auparavant | Référence exacte et groupe de prix lus ; aucune nouvelle requête UNIQLO pour ce test |
| Workflows | YAML et scripts Python embarqués analysés sans erreur |
| Extension | Manifest V3 et syntaxe JavaScript vérifiés |
| Paquet public | 10 fichiers autorisés ; aucun bootstrap privé ni favori de démonstration |
| Icônes | Génération PNG identique octet par octet aux 4 originales, répétable et sans dépendance |
| Tests GitHub | Étapes Python et JavaScript réussies dans l'exécution CI 40792139018 |
| Paquet GitHub | Artefact `uniqlo-alert-extension` 12861912680 produit, 25 086 octets |
| Intégrité du transfert | Les 21 fichiers de code/configuration/guide précédant les 2 documents finaux sont identiques aux sources locales par SHA Git |

Les régressions couvrent notamment :

- Première observation sans alerte, toutes les baisses suivantes, objectif informatif et absence de prix fictif.
- Mauvais groupe produit, prix invalide, erreurs réseau et conservation de la dernière lecture réussie.
- Blocages 403/429, `Retry-After`, suspension persistante, arrêt après erreurs réseau et reprise des favoris différés.
- Sauvegarde des alertes avant envoi, maintien en attente en cas d'échec, durée bornée et sauvegarde des confirmations Telegram.
- Ajouts simultanés, conflits de révision et absence de suppression locale lorsqu'un fichier distant disparaît ou devient invalide.
- Clé incorrecte, données chiffrées modifiées et gros historiques sans dépassement de pile JavaScript.

## Vérifications qui restent distinctes

La publication et les contrôles GitHub ont abouti. [Exécution CI réussie](https://github.com/werti4/uniqlo-alert/actions/runs/40792139018) sur le commit `febabcc091a0e2b41de35a65df670b2455f6d7b0`. L'artefact produit expire le 5 novembre 2026 ; les futurs résultats se consultent dans [Actions](https://github.com/werti4/uniqlo-alert/actions).

Le premier workflow scanner a exécuté sa vérification de configuration et ignoré les étapes de collecte, faute de clé et de favoris publiés. Ce résultat ne constitue pas une surveillance active.

La fiabilité d'un scan UNIQLO depuis un runner GitHub, l'installation effective de l'extension et la réception Telegram sur l'iPhone ne sont pas démontrées par ces tests. Elles demandent la configuration personnelle et une vérification réelle.

La vérification visuelle dans Chrome n'a pas été réalisée : les navigateurs de test n'ont pas pu atteindre le serveur d'aperçu local. La validation de syntaxe et des liaisons d'interface ne remplace pas ce contrôle.

## Fenêtre compacte 1.1.0 — validation locale

- 27 tests Python et 19 tests JavaScript réussis ; nouvelles régressions pour le résumé sans identifiants, le refus des commandes privilégiées depuis le site, la bascule sur la bonne fiche et les bascules concurrentes.
- Test Chromium sur pages synthétiques, avec API Chrome simulées et vrai gestionnaire background : apparition, ajout/retrait, réduction/réouverture, navigation SPA, catalogue et mode popup. Aucune requête UNIQLO ni Telegram. Captures desktop et écran étroit inspectées.
- Chargement réel d’extension bloqué dans le cloud par la politique administrateur ; installation réelle à vérifier dans Chrome après mise à jour et rechargement des pages UNIQLO.
- ZIP local 1.1.0 : 12 fichiers autorisés, archive intègre sans chiffrement ni ZIP imbriqué. Le workflow prépare désormais un artefact avec ces fichiers directement. Aucune exécution distante de cette nouvelle version n’est confirmée.

Publication 1.1.0 confirmée sur `main` le 29 octobre 2026 : commit `c35ff9eb71abecd1cd1d42826c3c0ed39eabb18e`. Le workflow [Vérifier le projet #2](https://github.com/werti4/uniqlo-alert/actions/runs/40797629957) a terminé avec succès et produit l’artefact `uniqlo-alert-extension` (29,6 Ko). La nouvelle archive contient directement les fichiers de l’extension. Installation dans le Chrome de l’utilisateur toujours à confirmer ; aucun scan réel ni Telegram vérifié dans cette étape.

## Correctif 1.1.1

La présentation 1.1.0 installée dans Chrome était cassée par le blocage du CSS inline sous `style-src 'self'`. Les captures simulées précédentes ne reproduisaient pas cette politique. Le correctif ne modifie pas la CSP : CSS externe pour les dimensions et feuille construite pour le Shadow DOM.

Validation locale : 27 tests Python, 19 tests JavaScript et test navigateur `tools/check_quick_ui.cjs` réussis. Ce dernier utilise le véritable HTML du popup et la CSP du manifeste : largeur 360 px, grille et couleurs appliquées, ajout/retrait et réduction/réouverture fonctionnels, aucune violation CSP. Les API Chrome sont simulées ; le test n’effectue aucune requête réelle UNIQLO/GitHub. Exécution avec Playwright 1.62.1 et Chromium disponible ; `PLAYWRIGHT_MODULE` et `CHROMIUM_EXECUTABLE` permettent de choisir les outils préinstallés. Les captures sont écrites dans `test-results/quick-ui/`. Le workflow CI installe Playwright et exécute aussi ce contrôle avant de produire le paquet.

Publication 1.1.1 confirmée : commit `10daff5b0cf8f47be9b82947694e02625cd0e3e2` sur `main`. [CI #3 réussie](https://github.com/werti4/uniqlo-alert/actions/runs/40798538628), y compris le test navigateur sous CSP, génération des icônes et artefact `uniqlo-alert-extension` (29,9 Ko). Le nouveau test échoue sur une copie de 1.1.0 avec le blocage de styles attendu. Mise à jour installée à confirmer chez l’utilisateur.

## Automatisation 5 minutes

Contrôle local des quatre combinaisons clé/favoris publiés : le scanner n’est autorisé à démarrer que lorsque les deux prérequis sont présents ; aucune valeur de clé n’est écrite. Scripts Python embarqués valides. 27 tests Python et 19 tests JavaScript réussis. Le calendrier demandé est `2-57/5 * * * *` ; cela ne garantit ni délai fixe par article ni temps réel. Telegram est explicitement facultatif et désactivé tant que la variable Actions UA_TELEGRAM_ENABLED ne vaut pas true. Un scan réel reste à vérifier après configuration personnelle.

Publication de l’automatisation confirmée : commit `f9caa99` sur `main`. [CI réussie](https://github.com/werti4/uniqlo-alert/actions/runs/40799781846), avec contrôle navigateur. [Exécution scanner](https://github.com/werti4/uniqlo-alert/actions/runs/40799781946) : contrôle de configuration réussi, installation et scan **ignorés** car les prérequis ne sont pas réunis. Aucun relevé réel effectué. L’absence de favoris publiés est vérifiée ; la présence du secret Actions n’a pas été établie indépendamment. L’utilisateur doit enregistrer sa clé existante en secret Actions et publier ses favoris via l’extension ; Telegram reste désactivé.
