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
