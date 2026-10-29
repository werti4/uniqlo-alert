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
| Fréquence initiale | 15 minutes visées, calendrier GitHub sans garantie de ponctualité |
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
