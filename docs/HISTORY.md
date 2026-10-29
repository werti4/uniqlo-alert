# Historique archivé — UNIQLO Alert

Archivé le 29 octobre 2026 (Europe/Paris). Les textes ci-dessous décrivent des états successifs, parfois dépassés. Ils ne constituent pas les instructions actuelles. Pour reprendre le travail, lire [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md), puis [DEVELOPMENT.md](DEVELOPMENT.md). Les blocages et autorisations historiques doivent être revérifiés avec les outils et résultats actuels.

## Ancien contexte, conservé intégralement

# Point de reprise — UNIQLO Alert

Mis à jour le 29 octobre 2026 (Europe/Paris).

## Objectif utilisateur

Construire et mettre en place sur `werti4/uniqlo-alert` une extension Chrome soignée pour gérer les favoris UNIQLO France et recevoir les baisses de prix sur iPhone. L'utilisateur a demandé la connexion à GitHub et autorisé la mise en place. Il demande de vérifier les choix entre agents et de garder un contexte cohérent pour éviter les boucles.

Le présent fichier synthétise les décisions. Ne pas confondre code écrit, code publié, configuration et fonctionnement vérifié.

## Exigences retenues

| Sujet | Décision |
| --- | --- |
| Coût | Logiciels et services gratuits ; aucun hébergement payant |
| Interface | Extension Chrome Manifest V3 avec tableau de bord |
| Articles | Favoris choisis par l'utilisateur ; pas de scan de tout le catalogue |
| Catalogue | UNIQLO France, devise EUR |
| Alertes | Toute baisse du prix valide précédemment observé, sans seuil minimum |
| Premier relevé | Référence initiale sans notification |
| Objectif facultatif | Indication budgétaire ; ne supprime aucune alerte de baisse |
| Exécution | GitHub Actions ; aucun scan automatique dans Chrome |
| Fréquence demandée | 5 minutes visées, calendrier GitHub sans garantie de ponctualité |
| iPhone | Telegram : bot personnel et conversation démarrée par l'utilisateur |
| Données distantes | AES-256-GCM ; favoris sur `main`, relevés sur `monitor-data` |
| Secrets | Clé et Telegram dans GitHub Actions ; PAT limité au dépôt dans l'extension |
| Taille/couleur | Préférences ; pas de promesse de stock par variante |
| Limite | 50 favoris ; lecture progressive avec durée bornée |

## Architecture à conserver

1. L'extension conserve les favoris localement et les publie explicitement, chiffrés, sur GitHub.
2. Le workflow déchiffre la liste avec le secret Actions, vérifie les pages publiques autorisées et compare les prix du même groupe produit.
3. Le scanner conserve le dernier prix valide et un historique limité. Les erreurs n'écrivent pas de prix de remplacement.
4. Les alertes sont sauvegardées dans l'état chiffré avant leur livraison Telegram. Les échecs restent dans la file.
5. L'extension récupère et déchiffre les relevés ; elle distingue date de synchronisation, tentative de scan et lecture effectivement réussie.

La publication des favoris protège la révision distante : une liste modifiée ailleurs doit être rechargée après export des changements locaux, sans écrasement silencieux.

## Fiabilité et protections

- Robots.txt vérifié, requêtes espacées, délais d'attente et durée totale bornés.
- Réponses 403/429 : pause persistée, respect de `Retry-After`, absence de contournement.
- Blocage, réseau et analyse des données : erreurs visibles avec prix conservé.
- Pas de clé ou jeton dans le dépôt public, les logs ou le paquet de l'extension.
- Le chiffrement Chrome/Python doit rester compatible ; tests aller-retour dédiés.
- Réussite CI, présence d'un PAT et succès de livraison Telegram sont trois vérifications différentes.

## État vérifié lors de la reprise

- Le dépôt GitHub public existe : `https://github.com/werti4/uniqlo-alert`.
- À la reprise, la branche distante `main` pointait encore sur le commit initial `d0e8b8985c2abed5c30ed9cf3f5f107655822cbf` ; la version de l'extension était uniquement locale.
- Le code local de l'extension et du scanner a été retrouvé ; il n'a pas été recréé depuis l'ancien ZIP.
- Quatre agents ont reçu des responsabilités distinctes : détection, infrastructure, interface, relecture indépendante. Le responsable intègre et vérifie leurs changements.
- Une ancienne lecture réussie d'une fiche ne démontre pas la fiabilité durable depuis un runner GitHub.

Les résultats de validation sont consignés dans `docs/VALIDATION.md`.

**État de livraison : code publié sur la branche publique `main` de `werti4/uniqlo-alert`.** L'utilisateur a autorisé le transfert et l'utilisation de sa session GitHub dans Chrome. La publication a été effectuée par l'éditeur GitHub : le push direct n'avait pas d'identifiants HTTPS et le connecteur refusait les écritures (403). Ne pas redemander les autorisations déjà données pour ce projet.

- CI GitHub réussie : [exécution 40792139018](https://github.com/werti4/uniqlo-alert/actions/runs/40792139018), commit de code `febabcc091a0e2b41de35a65df670b2455f6d7b0`.
- Les étapes de tests Python et JavaScript ont réussi, puis les icônes ont été générées et le paquet installable produit.
- Artefact `uniqlo-alert-extension`, identifiant `12861912680`, disponible dans cette exécution jusqu'au 5 novembre 2026. Les exécutions CI suivantes pourront produire un nouveau paquet.
- Les 21 fichiers publiés avant les deux présents documents ont été comparés à leurs sources locales par SHA Git : aucune différence.
- Le workflow scanner existe et sa vérification de configuration a réussi, mais les étapes de scan sont ignorées tant que la clé et les favoris publiés manquent. Aucune surveillance personnelle active ni livraison Telegram n'est confirmée.
- Les icônes PNG sont restaurées à l'identique depuis `tools/generate_icons.py`, sans dépendance ou accès réseau. CI le fait automatiquement ; une installation directement depuis les sources demande cette commande préalable.

## Configuration personnelle encore nécessaire

Ces éléments ne peuvent pas être déduits des fichiers du projet :

1. Installation locale de l'extension dans Chrome.
2. Création d'un jeton GitHub limité au dépôt, saisi uniquement dans l'extension.
3. Même clé de chiffrement dans l'extension et le secret `UA_ENCRYPTION_KEY`.
4. Bot Telegram créé, conversation démarrée, secrets `TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID` enregistrés.
5. Favoris publiés, relevé réel réussi depuis Actions, puis notification effectivement reçue sur l'iPhone.

Ne jamais écrire « surveillance active » tant que ces éléments ne sont pas vérifiés. Ne pas réclamer de jetons dans la conversation ; guider leur saisie dans les interfaces prévues.

## Suite utile

Les vérifications locales de cette version sont terminées : 27 tests Python et 17 tests JavaScript réussis, y compris la compatibilité du chiffrement. CI a ensuite réussi sur GitHub et fourni le paquet. Ne pas recommencer la conception, recréer le dépôt ou refaire le transfert initial. Prochaine étape : aider l'utilisateur à télécharger et installer l'artefact, puis configurer le jeton local, la clé et Telegram selon `SETUP.md`. Une mesure de fiabilité depuis GitHub permettra d'évaluer si le rythme peut être accéléré ; aucune promesse de cinq minutes garanties.

## Ce qui est hors périmètre

Scan massif du catalogue, achat automatique, contournement de CAPTCHA, proxies de rotation, récupération des sessions UNIQLO ou serveur payant. Le projet NAS/Maison et les autres projets personnels ne font pas partie de ce chantier.

## Priorité actuelle — installation Chrome

Le 29 octobre 2026, l’utilisateur demande de finaliser et installer l’extension Chrome, qui n’est pas encore installée sur son ordinateur. La configuration Telegram est explicitement reportée. Ne pas la demander comme préalable à l’installation ou à la gestion locale des favoris.

L’environnement cloud a validé 27 tests Python et 17 tests JavaScript. Les icônes ont été générées et le ZIP local a été contrôlé : 10 fichiers autorisés, aucune donnée privée. Aucun relevé réel ni envoi Telegram n’a été effectué. Le chargement de l’extension dans le Chromium de test cloud n’a pas abouti ; la validation visuelle et fonctionnelle dans le Chrome de l’utilisateur reste à effectuer. Le paquet peut être obtenu depuis une exécution réussie de « Vérifier le projet » dans GitHub Actions.

Étapes manuelles restantes : télécharger et décompresser le paquet, ouvrir chrome://extensions, activer le mode développeur, charger le dossier contenant manifest.json et vérifier l’ouverture du tableau de bord. La connexion GitHub et le secret UA_ENCRYPTION_KEY sont nécessaires aux scans cloud, mais pas à l’installation ni à l’ajout local d’un favori.

## Fenêtre compacte — version 1.1.0

Demande utilisateur : afficher automatiquement une petite fenêtre dès l’ouverture d’une page UNIQLO ; ajouter ou retirer en un clic l’article de la fiche ouverte ; voir les fonctions principales sans ouvrir le grand tableau de bord. Implémentation : script de contenu sur www.uniqlo.com, interface isolée par Shadow DOM, bouton de réduction/réouverture, popup Chrome et accès aux favoris/baisses/alertes/réglages. Seules les fiches France sont prises en charge pour l’ajout. Les changements restent locaux jusqu’à publication explicite. Aucun scan local ou envoi Telegram ajouté. La demande antérieure sur la fréquence Actions reste distincte, sans modification du calendrier dans cette étape.

Le site ne reçoit qu’un résumé restreint : aucune clé ni jeton. Les commandes privilégiées sont refusées depuis les scripts de contenu. L’artefact Actions inclut les deux nouveaux fichiers et fournit directement les fichiers d’extension, sans ZIP imbriqué.

Validation du 29 octobre 2026 : 27 tests Python et 19 tests JavaScript réussis. Dans Chromium, test d’interface sur pages synthétiques avec API Chrome simulées et vrai gestionnaire background : apparition, ajout/retrait, compteurs, réduction/réouverture, navigation SPA et catalogue réussis sans erreur JavaScript. Captures desktop et écran étroit inspectées. Le chargement réel d’une extension décompressée dans ce cloud est interdit par la politique administrateur (diagnostic CDP explicite) ; aucune modification de cette politique. La validation de l’installation réelle reste à faire dans le Chrome de l’utilisateur. Cette version est préparée localement ; aucune publication GitHub n’est démontrée pour ces changements.

Publication 1.1.0 confirmée sur `main` le 29 octobre 2026 : commit `c35ff9eb71abecd1cd1d42826c3c0ed39eabb18e`. Le workflow [Vérifier le projet #2](https://github.com/werti4/uniqlo-alert/actions/runs/40797629957) a terminé avec succès et produit l’artefact `uniqlo-alert-extension` (29,6 Ko). La nouvelle archive contient directement les fichiers de l’extension. Installation dans le Chrome de l’utilisateur toujours à confirmer ; aucun scan réel ni Telegram vérifié dans cette étape.

## Correctif 1.1.1 — styles du popup

La capture de l’utilisateur confirme l’installation de 1.1.0 mais montre un popup étroit sans styles. Cause : le manifeste impose `style-src 'self'` et bloque les balises `<style>` inline du document et du Shadow DOM. Les tests précédents utilisaient des pages sans cette politique et n’avaient pas détecté ce défaut.

Correction : dimensions dans `quick-popup.css` externe, styles du Shadow DOM via feuille CSS construite, sans assouplir la CSP. Le paquet doit inclure ce nouveau fichier (13 fichiers). Test de régression navigateur `tools/check_quick_ui.cjs`, également ajouté à CI : véritable HTML du popup servi avec la CSP exacte du manifeste, API Chrome simulées, styles calculés, largeur 360 px, grille, couleurs, clics et absence de violations CSP vérifiés. Le cloud interdit toujours le chargement réel d’extensions ; la vérification de la nouvelle version installée reste à faire dans le Chrome de l’utilisateur.

Publication 1.1.1 confirmée : commit `10daff5b0cf8f47be9b82947694e02625cd0e3e2` sur `main`. [CI #3 réussie](https://github.com/werti4/uniqlo-alert/actions/runs/40798538628), y compris le test navigateur sous CSP, génération des icônes et artefact `uniqlo-alert-extension` (29,9 Ko). Le nouveau test échoue sur une copie de 1.1.0 avec le blocage de styles attendu. Mise à jour installée à confirmer chez l’utilisateur.

## Automatisation GitHub — 5 minutes, Telegram reporté

L’utilisateur demande la configuration de l’automatisation. Le workflow `scan.yml` vise désormais un lancement aux minutes :02, :07, …, :57 (`2-57/5 * * * *`), sans garantie de temps réel. Les favoris publiés déclenchent également un scan ; le lancement manuel reste possible. Conservation de la sérialisation, des limites de durée, des pauses en cas de blocage et du stockage chiffré. Les notifications Telegram sont désactivées par défaut et nécessitent ultérieurement `UA_TELEGRAM_ENABLED=true` dans les variables Actions, en plus des deux secrets. La clé `UA_ENCRYPTION_KEY` et les favoris chiffrés restent les seuls prérequis personnels du scanner.

Avant publication, aucun fichier `data/watchlist.enc.json` et aucune branche `monitor-data` n’étaient présents sur le dépôt distant. La lecture de la liste des secrets via l’API GitHub n’est pas accessible depuis cet environnement ; ne pas en déduire l’absence de clé. Ne pas demander de secret dans le chat ni générer une clé différente de celle du Chrome utilisateur. Étapes manuelles : copier la clé depuis l’extension vers le secret Actions, puis publier les favoris.

Validation locale : quatre cas du contrôle de configuration (clé/fichier présents ou absents) réussis sans valeur sensible dans le résumé ; scripts Python embarqués compilés ; 27 tests Python et 19 tests JavaScript réussis. L’extension 1.1.2 affiche la nouvelle fréquence et ne présente plus Telegram comme bloquant lorsque les relevés sont réussis. Aucun relevé réel ni message Telegram confirmé à ce stade.

Publication de l’automatisation confirmée : commit `f9caa99` sur `main`. [CI réussie](https://github.com/werti4/uniqlo-alert/actions/runs/40799781846), avec contrôle navigateur. [Exécution scanner](https://github.com/werti4/uniqlo-alert/actions/runs/40799781946) : contrôle de configuration réussi, installation et scan **ignorés** car les prérequis ne sont pas réunis. Aucun relevé réel effectué. L’absence de favoris publiés est vérifiée ; la présence du secret Actions n’a pas été établie indépendamment. L’utilisateur doit enregistrer sa clé existante en secret Actions et publier ses favoris via l’extension ; Telegram reste désactivé.

## Vérification des promotions UNIQLO

Demande utilisateur : examiner comment UNIQLO déclare un article en promotion. Le code actuel lit `prices.base` et `prices.promo` dans les données SSR du groupe produit exact ; l’interface déclare « Promotion affichée » si `regularCents > priceCents`. Une baisse depuis le dernier relevé est une notion différente : le premier relevé d’un article déjà en promotion ne crée pas d’alerte. Trois vérifications synthétiques (promo inférieure, prix égaux, promo absente) réussies.

Vérification en direct non effectuée : la requête à robots.txt est refusée par le proxy de l’environnement (CONNECT HTTP 403), avant accès à UNIQLO. Le domaine `www.uniqlo.com` a été ajouté au brouillon réseau en préservant les préréglages ; l’utilisateur doit enregistrer puis publier cet environnement pour appliquer la configuration. Les éventuels marquages d’offre temporaire, de prix membre et les dates de promotion restent à vérifier sur des fiches réelles ; ne pas les présenter comme pris en charge ni comme constatés actuellement. Aucun changement de détection publié dans cette étape.


## Ancien journal de validation, conservé intégralement

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


## Archive avant le premier déploiement Cloudflare — 29 octobre 2026

Les paragraphes suivants décrivent les étapes antérieures ; le contexte courant et le guide Cloudflare font foi.

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

## Réception immédiate Telegram — webhook préparé, non déployé

L’utilisateur demande maintenant des commandes sans lancer manuellement Actions. Un récepteur Cloudflare Workers + Durable Object SQLite est préparé dans `telegram-webhook/`. Il valide le header secret Telegram et le propriétaire privé, persiste uniquement id/commande dans une file, demande un workflow_dispatch avec un PAT Actions write limité au dépôt, puis envoie un accusé de réception. Le résultat final reste soumis à la file d’attente GitHub. La file persistante conserve les commandes si GitHub remplace un run pending ; un rappel à dix minutes relance une file non vidée. Limite 20 commandes, trois par passage, un scan par passage.

Quand la variable Actions UA_TELEGRAM_WEBHOOK_URL est renseignée, le lecteur utilise /pending et /ack authentifiés par UA_TELEGRAM_WEBHOOK_SECRET et n’appelle plus getUpdates. Le schedule du lecteur est ignoré dans ce mode. Le scanner périodique, les règles de prix et l’extension sont inchangés. Aucun chemin déclenchant un scan au push modifié, aucun workflow manuel lancé.

Déploiement et activation **non effectués** : aucun outil Cloudflare connecté, identité sortante ou variable Cloudflare présente dans le cloud. L’utilisateur indique ne pas avoir de compte Cloudflare et demande un fonctionnement sur le palier gratuit. Étapes externes requises : compte Workers/DO sur palier choisi, déploiement, secrets Cloudflare et GitHub, puis enregistrement du webhook via le script local `tools/register_telegram_webhook.py` (saisie masquée). Guide complet dans [telegram-webhook/README.md](../telegram-webhook/README.md). Ne pas demander de jeton dans le chat ni réutiliser le jeton Telegram révoqué. La publication du code ne constitue pas l’hébergement du service.

Validation : 49 tests Python et 23 tests Node réussis avec réseau simulé ; compilation officielle Wrangler 4.155.0 en --dry-run réussie, binding SQLite reconnu. Ni URL publique active, ni liaison webhook Telegram, ni accusé/résultat immédiat en situation réelle vérifiés. Le palier gratuit Cloudflare dépend de ses quotas/conditions ; aucune gratuité ou disponibilité illimitée promise.

Préparation webhook publiée (`5c74690`, ajustement de confidentialité `e3d18c8`). [CI 40844189873 réussie](https://github.com/werti4/uniqlo-alert/actions/runs/40844189873), suites Python/JS et contrôle navigateur. Worker assemblé en dry-run mais **non déployé**, webhook Telegram **non enregistré**, réception immédiate **non active**. Les identifiants Cloudflare sont absents et aucun connecteur de déploiement n’est disponible ; il reste la création/connexion du compte, le déploiement et la saisie sécurisée des secrets selon telegram-webhook/README.md.

## Objectif retenu : scans horaires Cloudflare + commandes à la demande

L’utilisateur souhaite désormais au moins une demande de scan automatique par heure depuis Cloudflare, puis des /scan Telegram selon ses besoins. Le Worker possède un handler scheduled et le cron `17 * * * *` ; il dispatch scan.yml sans envoyer de message de routine. Les commandes continuent de déclencher telegram-commands.yml. Événement horaire confirmé mémorisé dans le Durable Object pour éviter les doublons ; erreurs non validées comme succès. Endpoint /hourly interne uniquement, absent des routes HTTP publiques.

Activation explicite requise : HOURLY_SCAN_ENABLED="true" après déploiement et secrets. Valeur par défaut "false" pour ne pas annoncer de service actif prématurément. Cloudflare, compte et secrets toujours indisponibles ici : aucune activation ni vrai scan horaire. L’ancien cron GitHub cinq minutes n’est pas modifié à ce stade, pour préserver le fonctionnement existant et éviter un scan de push ; il faudra retirer uniquement on.schedule après validation Cloudflare si une seule horloge est souhaitée. GitHub affichera workflow_dispatch pour les lancements automatiques issus de Cloudflare.

Validation locale : 49 tests Python, 26 tests Node réussis, dont trois tests du calendrier horaire (dispatch vers scanner distinct des commandes, déduplication, switch désactivé, route publique refusée, échec non enregistré). Le service reste préparé et non hébergé ; les disponibilités externes et le blocage UNIQLO peuvent empêcher un scan complet. Aucun scan réel lancé par l’agent.

Préparation horaire publiée (`ff9214e`), [CI 40846436147 réussie](https://github.com/werti4/uniqlo-alert/actions/runs/40846436147), 49 tests Python et 26 tests Node. Wrangler --dry-run réussi avec le binding Durable Object et HOURLY_SCAN_ENABLED=false. Aucun déploiement, événement horaire réel ni scan forcé. Étape externe restante : compte Cloudflare, secrets, déploiement et activation explicite.

Consolidation du contrat Telegram : catalogue partagé /logs et /scan, reconnaissance et accusés dérivés du catalogue côté Cloudflare, autorisation/bornes maintenues côté exécutant. Tests de couverture de chaque commande et rejet d’un traitement non implémenté ajoutés : 51 tests Python, 27 tests Node réussis localement. Aucun changement du calendrier ou scan forcé ; aucun déploiement.

Contrat et catalogue des commandes publiés au commit `128fff1`. [Job CI 40853282759](https://github.com/werti4/uniqlo-alert/actions/runs/40853282759) : toutes les étapes, y compris tests et contrôle navigateur, terminées avec succès. Catalogue inclus dans le Worker lors du dry-run Wrangler. Cloudflare reste non déployé : aucun service actif ni réponse réelle supplémentaire annoncés.

## Commande `/favoris` — ajout au catalogue Cloudflare

Demande utilisateur : tous les favoris avec prix et pastille rouge pour les promotions. Commande /favoris ajoutée au catalogue unique Cloudflare (reconnaissance et accusé dérivés automatiquement), traitement privé délégué à tools/telegram_favorites.py via le runner de commandes. Liste les favoris publiés actifs ET pausés, prix actuel/base connus, 🔴 promotion au dernier relevé, ⚪ absence de promotion confirmée, ⚫ prix absent, date Paris, ancienneté et dernière erreur. Pagination sous 3500 caractères par message. Ne lit pas le stockage Chrome, ne publie/réécrit pas de favoris, ne lance pas de scan. Échec de lecture de la liste distinct d’une liste vide ; si l’état est inaccessible, les noms restent disponibles sans prix inventés.

L’utilisateur a demandé si un scan avant chaque /favoris serait coûteux. Recommandation communiquée : garder /favoris en lecture seule ; demander /scan puis /favoris lorsqu’une actualisation est souhaitée. Le travail de scan est principalement côté GitHub/UNIQLO et soumis aux pauses ; pas de scan implicite ajouté à /favoris.

Validation locale : 57 tests Python, 27 tests Node réussis, dont six nouveaux tests sur promotions, prix manquants/anciens/erreurs, liste vide/illisible, 50 favoris paginés, accès propriétaire et absence de scan. Cloudflare toujours non déployé selon le dernier état confirmé. Aucun scan ni message réel forcés. Inventaire courant : /logs, /scan, /favoris.

/favoris publié (`f99c27d`), [job CI 40854426246](https://github.com/werti4/uniqlo-alert/actions/runs/40854426246) terminé avec toutes les étapes réussies, 57 tests Python et 27 tests Node. Catalogue inclus dans l’assemblage Wrangler --dry-run réussi. Aucun scan ni déploiement réel effectués ; la commande sera active après configuration Cloudflare et validation d’une réponse privée réelle.
