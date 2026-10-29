# Configurer sa surveillance

## 1. Installer l'extension

Dans [Actions](https://github.com/werti4/uniqlo-alert/actions), ouvrir une exécution réussie de **Vérifier le projet**, puis télécharger l'artefact `uniqlo-alert-extension`. Décompresser l'archive. Si elle contient `uniqlo-alert-extension.zip`, décompresser aussi ce second fichier pour obtenir `manifest.json`.

Ouvrir `chrome://extensions`, activer **Mode développeur**, puis **Charger l'extension non empaquetée**. Choisir le dossier contenant `manifest.json`. Épingler l'extension si souhaité, puis cliquer sur son icône.

Pour une installation depuis les sources, exécuter d'abord `python3 tools/generate_icons.py` à la racine du dépôt téléchargé, puis sélectionner le dossier `extension/`. L'artefact Actions contient déjà les icônes générées. Après une mise à jour des fichiers, cliquer sur **Actualiser** dans `chrome://extensions`.

### La petite fenêtre UNIQLO

Après une mise à jour, cliquez sur **Actualiser** dans `chrome://extensions`, puis rechargez les pages UNIQLO déjà ouvertes. La fenêtre apparaît automatiquement en bas à droite sur `www.uniqlo.com`. Sur une fiche **UNIQLO France**, son bouton ajoute ou retire l’article ouvert en un clic. Sur les autres pages, elle conserve l’aperçu et l’accès au tableau de bord. Aucun prix n’est inventé avant un relevé du scanner.

Les compteurs ouvrent les favoris, les articles en baisse ou les alertes. Le bouton « − » réduit la fenêtre ; le bouton « UNIQLO Alert » la rouvre. L’icône Chrome ouvre également une petite fenêtre, depuis n’importe quel site. Les réglages et le tableau de bord complet restent accessibles.

Les modifications restent locales jusqu’à leur publication dans le tableau de bord. Telegram peut être configuré plus tard ; il ne bloque ni l’installation ni la gestion des favoris.

La nouvelle version demande l’accès aux pages `www.uniqlo.com` pour afficher la fenêtre automatiquement. Chrome peut demander de confirmer cet accès après la mise à jour. Aucun accès automatique aux autres sites n’est ajouté.

## 2. Créer l'accès GitHub de l'extension

Créer un **fine-grained personal access token** depuis les paramètres GitHub, dans **Developer settings → Personal access tokens → Fine-grained tokens**.

- Propriétaire : `werti4`.
- Dépôt sélectionné uniquement : `uniqlo-alert`.
- **Contents : Read and write** pour lire les relevés et publier les favoris chiffrés.
- **Actions : Read and write** pour consulter les exécutions et demander un scan manuel.
- Choisir une expiration et prévoir son renouvellement. Aucun droit d'administration ou de modification des workflows n'est nécessaire pour l'extension.

Dans les réglages de l'extension, laisser `werti4/uniqlo-alert` et `main`, saisir le jeton et enregistrer. Le jeton reste dans le profil Chrome local ; ne pas le publier, l'envoyer dans un chat ou le placer dans un fichier source.

## 3. Enregistrer la clé de chiffrement

L'extension génère une clé sur l'appareil. Dans ses réglages, utiliser **Copier la clé** et en garder une copie dans un emplacement privé.

Ouvrir les [secrets Actions du dépôt](https://github.com/werti4/uniqlo-alert/settings/secrets/actions), puis **New repository secret** :

| Nom du secret | Valeur |
| --- | --- |
| `UA_ENCRYPTION_KEY` | La clé exacte copiée depuis l'extension |

La clé doit être identique des deux côtés. Ne pas la remplacer après publication des favoris : une clé différente ne peut pas lire les anciens relevés. Elle est également nécessaire pour configurer un deuxième appareil.

## 4. Configurer Telegram sur iPhone (facultatif pour les relevés)

Pour démarrer les relevés sans Telegram, passez directement à l’étape 5.

1. Installer Telegram et autoriser les notifications dans **Réglages iPhone → Notifications → Telegram**. Vérifier aussi le mode Concentration si les notifications sont silencieuses.
2. Dans Telegram, ouvrir le compte officiel [@BotFather](https://t.me/BotFather), envoyer `/newbot` et suivre ses instructions.
3. Conserver le jeton fourni dans un endroit privé. Il sera enregistré dans GitHub, jamais dans le code de l'extension.
4. Ouvrir la conversation de son nouveau bot et appuyer sur **Démarrer**, puis lui envoyer un message, par exemple `Bonjour`.
5. Déterminer son `chat_id` avec l'API Telegram, comme indiqué ci-dessous.
6. Créer les deux secrets Actions :

| Nom du secret | Valeur |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Jeton fourni par BotFather |
| `TELEGRAM_CHAT_ID` | Identifiant numérique de la conversation personnelle |

### Trouver son chat_id sans exposer le jeton dans une URL de navigateur

Si Python 3 est installé, exécuter ce petit script dans un terminal local. Le jeton est demandé sans affichage et n'est pas écrit dans l'historique de commandes. Envoyer d'abord un message au bot ; sinon le résultat peut être vide.

```python
import getpass
import json
import urllib.request

token = getpass.getpass("Jeton du bot Telegram : ").strip()
try:
    request = urllib.request.Request(
        "https://api.telegram.org/bot" + token + "/getUpdates",
        data=b"{}", headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        result = json.load(response)
    chats = {
        update["message"]["chat"]["id"]
        for update in result.get("result", [])
        if update.get("message", {}).get("chat", {}).get("type") == "private"
    }
    print("Identifiant(s) de conversation privée :", sorted(chats))
    if not chats:
        print("Envoyer un nouveau message au bot, puis relancer.")
except Exception:
    print("Lecture impossible. Vérifier le jeton et la connexion sans les publier.")
```

N'utiliser que son propre identifiant de conversation. En cas de divulgation du jeton, le révoquer auprès de BotFather et mettre à jour le secret.

### Tester puis activer Telegram

Les scans de prix n’exigent pas Telegram. Les notifications sont désactivées par défaut.

Après avoir enregistré les deux secrets, ouvrir [Tester Telegram](https://github.com/werti4/uniqlo-alert/actions/workflows/test-telegram.yml), puis **Run workflow → main → Run workflow**. Ce lancement manuel vérifie le bot et la conversation privée, puis envoie un message explicitement marqué « test ». Il ne modifie ni les favoris, ni les prix, ni l’historique. Il ne nécessite pas la clé de chiffrement et fonctionne avant l’activation des alertes automatiques. Aucun jeton ou identifiant personnel n’est affiché dans les logs. Vérifier la réception du message et de la notification sur l’iPhone ; le succès de l’API seul ne prouve pas que les notifications iOS sont autorisées.

Lors de l’activation automatique, les alertes encore en attente dans l’état chiffré peuvent être livrées au prochain scan : ce ne sont pas forcément des baisses survenues à l’instant.

Une fois le message de test reçu et les deux secrets enregistrés, créer la **variable Actions** `UA_TELEGRAM_ENABLED` avec la valeur `true` dans les paramètres du dépôt → Secrets and variables → Actions → Variables. Sans cette activation explicite, le workflow ne transmet pas les identifiants Telegram au scanner et aucun message n’est envoyé.

## 5. Ajouter et publier les favoris

Depuis une fiche UNIQLO France, cliquer sur l'extension : elle propose l'article ouvert. On peut aussi utiliser **Ajouter un article** avec le lien complet de la fiche.

Les changements sont locaux jusqu'au clic sur **Publier les favoris**. Cette action envoie uniquement la liste chiffrée. Les scans suivants utilisent la liste publiée ; mettre un favori en pause demande aussi de publier le changement.

La couleur et la taille souhaitées restent indicatives. L'objectif de prix est facultatif : **toutes les baisses restent signalées**, même au-dessus de cet objectif.

## 6. Vérifier le fonctionnement réel

Dans les réglages de l'extension, cliquer sur **Lancer un scan GitHub**, puis consulter l'exécution dans Actions et actualiser l'extension après sa fin.

- Une date de dernière lecture valide et un prix doivent apparaître sur chaque article lu.
- Le premier relevé ne déclenche aucune alerte de baisse ; il sert de référence.
- Une simple présence des secrets Telegram indique une configuration déclarée, pas une réception vérifiée sur l'iPhone.
- La première baisse détectée doit apparaître dans **Mes alertes** avec son statut de livraison. L'obtention d'un message Telegram confirme alors la livraison ; la réception effective sur l'iPhone reste à constater sur l'appareil.

Le scan planifié vise 5 minutes entre lancements, sans ponctualité garantie. La durée de lecture, les erreurs et les pauses peuvent allonger le délai réel par article.

## Dépannage

| Symptôme | Vérification utile |
| --- | --- |
| Configuration requise dans Actions | Présence de `UA_ENCRYPTION_KEY` et d'une liste de favoris publiée |
| Impossible de déchiffrer | Même clé dans l'extension et le secret, pas de nouvelle clé générée |
| Jeton refusé | Expiration, accès au bon dépôt, permissions Contents et Actions |
| Conflit de favoris | Exporter les changements locaux, recharger la version distante, puis réappliquer les changements utiles |
| HTTP 403/429 UNIQLO | Attendre la fin de la pause ; ne pas multiplier les scans manuels |
| Dernier prix ancien | Lire l'erreur par article et les dernières exécutions GitHub |
| Alerte en attente | Bot démarré, jeton/chat_id corrects, secrets Telegram présents |
| Alerte envoyée sans notification iPhone | Ouvrir Telegram, vérifier notifications, conversation en sourdine et Concentration |
| Plus de lancement automatique | Vérifier l'activation du workflow et une éventuelle désactivation après 60 jours sans activité |

Ne jamais copier les secrets dans une issue publique ou les logs. Le code ne contient aucun mécanisme de contournement des blocages UNIQLO.

## Commande Telegram `/logs`

Dans la conversation privée de votre bot, envoyer `/logs`. Le workflow **Commandes Telegram** est configuré pour consulter les messages toutes les cinq minutes demandées, à :04, :09, …, :59, avec les délais/omissions possibles de GitHub. Il utilise les secrets existants et `UA_TELEGRAM_ENABLED=true`. Aucun serveur permanent ni nouveau jeton nécessaire.

La réponse présente un résumé diagnostique : dernière tentative et lecture valide reçue (heures de Paris), nombres de réussites/erreurs/différés du dernier état sauvegardé, statut d’erreur/pause et cinq dernières exécutions Actions avec liens. Les logs bruts se consultent sur GitHub. Les valeurs d’erreur libres, noms d’articles et identifiants sensibles ne sont pas recopiés. Les données sauvegardées peuvent être anciennes, même si un scan plus récent a eu lieu.

Seuls les messages de la conversation privée et de l’utilisateur correspondant à `TELEGRAM_CHAT_ID` sont autorisés. Le curseur de traitement est chiffré séparément dans `monitor-data:data/telegram-commands.enc.json` ; l’historique scanner reste intact. Ne pas faire tourner un autre lecteur `getUpdates` ou un webhook en parallèle. Au maximum trois réponses par passage ; en cas d’interruption après envoi et avant sauvegarde, une réponse peut exceptionnellement être répétée. Telegram ne conserve les messages à récupérer que pendant une durée limitée (24 h).

**Cette commande ne lance aucun scan UNIQLO.** L’absence de lancements planifiés constatée sur le dépôt peut aussi empêcher une réponse automatique. Sa présence dans le code ne prouve pas une exécution réelle ; aucun lancement manuel n’est effectué par l’agent conformément à la demande utilisateur.

## Commande Telegram `/scan`

Envoyer `/scan` dans votre conversation privée avec le bot (ou `/scan@NomDuBot`). Au prochain passage du workflow **Commandes Telegram**, il répond « Scan en cours », exécute une vérification des **favoris actifs publiés**, puis envoie « Scan terminé » et les articles actuellement en promotion : nom, prix actuel, prix de base et lien. Les promotions déjà présentes au premier relevé sont incluses dans ce bilan demandé ; cela ne change pas la règle des alertes automatiques de baisse.

« Aucun article en promo » est envoyé seulement si tous les favoris actifs ont été vérifiés pendant ce scan, avec une comparaison de prix valide. En cas de blocage, erreur, article différé ou prix de base absent, le résultat est explicitement incomplet. Les vieux prix ne sont pas présentés comme des promotions nouvellement vérifiées. Les pauses et robots.txt sont respectés : la commande ne contourne pas un blocage.

La commande n’est pas instantanée : elle dépend de la lecture différée des messages par Actions. Le problème de planification connu peut aussi bloquer cette lecture. Un seul scan par passage est autorisé ; une demande est enregistrée comme consommée avant le lancement afin de ne pas répéter un scan automatiquement si une réponse Telegram échoue. Si l’exécution est interrompue, consulter /logs et Actions avant de renvoyer volontairement /scan.

Les workflows de commandes et de scanner partagent désormais le groupe de concurrence `uniqlo-monitor` pour protéger l’historique chiffré. Ne pas lancer un autre lecteur getUpdates. Aucun nouveau secret ni changement d’extension requis.

## Réponse sans lancement manuel : mode webhook

Voir [le guide de déploiement Cloudflare](../telegram-webhook/README.md). Le Worker et sa file SQLite sont **déployés**, les cinq secrets requis sont maintenant présents (noms/types vérifiés), accès et liaison Actions/webhook validés, premier scan horaire naturel confirmé. Voir [le relais Codex](CODEX_HANDOFF.md). Un compte Workers avec Durable Object SQLite et une configuration de secrets sont nécessaires. L’accusé de réception sera rapide après activation ; l’exécution du scan restera soumise aux délais GitHub Actions. Le Worker inclut aussi un calendrier horaire Cloudflare, à activer explicitement après déploiement selon le guide. L’ancien calendrier GitHub reste distinct tant que sa migration n’a pas été effectuée. Aucun jeton dans le chat.

## Règle pour les commandes à venir

Toutes les commandes Telegram doivent être intégrées à Cloudflare et au [catalogue partagé](../telegram-webhook/commands.json), selon [TELEGRAM_COMMANDS.md](TELEGRAM_COMMANDS.md). Une nouvelle commande implique tests, documentation et redéploiement du Worker ; ne pas ajouter uniquement un script Python ou un bouton de lancement Actions. Le Worker Cloudflare est déployé ; consulter le contexte courant pour la liaison et les validations restantes.

## Commande `/favoris`

Afficher tous les favoris **publiés** sur GitHub, y compris ceux en pause, avec les derniers prix connus : 🔴 promotion au dernier relevé (prix inférieur au prix de base), ⚪ pas de promotion confirmée, ⚫ prix indisponible. La date du relevé et un avertissement pour les prix anciens/en erreur évitent de présenter un ancien prix comme actuel. La liste est découpée en plusieurs messages si nécessaire. Les favoris locaux non publiés ne sont pas accessibles au bot.

La commande ne lance aucun scan. Pour demander une nouvelle vérification, utiliser /scan, attendre sa fin puis /favoris. Cela évite de multiplier les lectures UNIQLO à chaque consultation. Le surcoût d’un scan est surtout dans le runner GitHub et les requêtes UNIQLO, pas dans le récepteur Cloudflare. L’ajout au catalogue est publié ; le Worker est déployé, mais il faut terminer les accès et valider une réponse réelle avant d’annoncer la commande active.
