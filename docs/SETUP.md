# Configurer sa surveillance

**Pour werti4/uniqlo-alert, la configuration est déjà terminée.** Webhook Cloudflare et scan horaire à `:17` actifs, premier déclenchement naturel validé ; aucun secret à recréer. Ce guide sert à une nouvelle installation ou à la maintenance. [État courant](PROJECT_CONTEXT.md) et [contrôle depuis iPhone](../telegram-webhook/README.md#contrôle-et-maintenance-depuis-iphone).

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

### Identité et jeton existants

Pour ce dépôt, le bot renouvelé et le propriétaire privé sont déjà validés. Conserver les valeurs stockées ; ne pas recréer le bot ni utiliser un ancien token révoqué. Le token est distinct du secret partagé de webhook. En cas de nouvelle installation, établir l’identifiant du compte personnel avant l’activation avec les outils sécurisés disponibles ; ne pas mettre le token dans une URL Safari ou dans le chat.

Ne pas appeler `getUpdates` sur ce bot : son webhook est actif. Le mode polling est uniquement un retour arrière après retrait contrôlé du webhook, selon le guide Cloudflare.

### Test facultatif pour une nouvelle installation

Les scans de prix n’exigent pas Telegram. Les notifications sont désactivées par défaut pour une nouvelle installation ; elles sont déjà activées sur ce dépôt. **Ne lancer le test ci-dessous que sur demande explicite : il envoie un vrai message.** Il n’est pas nécessaire pour une reprise ou une vérification en lecture seule.

Après avoir enregistré les deux secrets, ouvrir [Tester Telegram](https://github.com/werti4/uniqlo-alert/actions/workflows/test-telegram.yml), puis **Run workflow → main → Run workflow**. Ce lancement manuel vérifie le bot et la conversation privée, puis envoie un message explicitement marqué « test ». Il ne modifie ni les favoris, ni les prix, ni l’historique. Il ne nécessite pas la clé de chiffrement et fonctionne avant l’activation des alertes automatiques. Aucun jeton ou identifiant personnel n’est affiché dans les logs. Vérifier la réception du message et de la notification sur l’iPhone ; le succès de l’API seul ne prouve pas que les notifications iOS sont autorisées.

Lors de l’activation automatique, les alertes encore en attente dans l’état chiffré peuvent être livrées au prochain scan : ce ne sont pas forcément des baisses survenues à l’instant.

Une fois le message de test reçu et les deux secrets enregistrés, créer la **variable Actions** `UA_TELEGRAM_ENABLED` avec la valeur `true` dans les paramètres du dépôt → Secrets and variables → Actions → Variables. Sans cette activation explicite, le workflow ne transmet pas les identifiants Telegram au scanner et aucun message n’est envoyé.

## 5. Ajouter et publier les favoris

Depuis une fiche UNIQLO France, cliquer sur l'extension : elle propose l'article ouvert. On peut aussi utiliser **Ajouter un article** avec le lien complet de la fiche.

Les changements sont locaux jusqu'au clic sur **Publier les favoris**. Cette action envoie uniquement la liste chiffrée. Les scans suivants utilisent la liste publiée ; mettre un favori en pause demande aussi de publier le changement.

La couleur et la taille souhaitées restent indicatives. L'objectif de prix est facultatif : **toutes les baisses restent signalées**, même au-dessus de cet objectif.

## 6. Vérifier le fonctionnement réel

Attendre le prochain scan naturel Cloudflare à `:17`, consulter l’exécution dans Actions, puis actualiser l’extension. Une demande `/scan` depuis Telegram reste possible pour actualiser volontairement ; aucun scan manuel n’est nécessaire pour valider une reprise.

- Une date de dernière lecture valide et un prix doivent apparaître sur chaque article lu.
- Le premier relevé ne déclenche aucune alerte de baisse ; il sert de référence.
- Une simple présence des secrets Telegram indique une configuration déclarée, pas une réception vérifiée sur l'iPhone.
- La première baisse détectée doit apparaître dans **Mes alertes** avec son statut de livraison. L'obtention d'un message Telegram confirme alors la livraison ; la réception effective sur l'iPhone reste à constater sur l'appareil.

Cloudflare demande un scan par heure à la minute 17 (`17 * * * *`). Les anciens calendriers GitHub sont retirés. Démarrage Actions, durée de lecture, erreurs et pauses peuvent allonger le délai réel par article.

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
| Plus de lancement automatique | Vérifier cron Cloudflare, `HOURLY_SCAN_ENABLED=true`, expiration du PAT Worker et derniers runs Actions ; ne pas rétablir un calendrier concurrent |

Ne jamais copier les secrets dans une issue publique ou les logs. Le code ne contient aucun mécanisme de contournement des blocages UNIQLO.

## Utiliser les commandes Telegram

Envoyer les commandes dans la conversation privée du bot. Cloudflare vérifie le propriétaire, conserve la commande, accuse réception puis déclenche automatiquement Actions. Les suffixes `/commande@NomDuBot` sont acceptés pour le bon bot. Aucun lancement manuel de workflow requis ; le résultat peut attendre un runner GitHub.

| Commande | Utilisation |
| --- | --- |
| `/logs` | Diagnostic, dates du dernier état, erreurs/pauses et cinq derniers runs avec liens ; aucun scan |
| `/scan` | Vérification des favoris actifs publiés, état puis promotions avec prix de référence et lien ; inclut les promos présentes dès l’ajout |
| `/favoris` | Tous les favoris publiés, actifs ou pausés, derniers prix connus et dates, 🔴 promotion, ⚪ absence confirmée, ⚫ prix absent ; aucun scan |

`/scan` n’annonce aucune promotion seulement si la vérification est complète ; erreurs, articles différés ou prix de base manquant donnent un bilan incomplet explicite. Il respecte les pauses et ne contourne aucun blocage. Un seul scan par passage ; une demande consommée n’est pas rejouée automatiquement après une erreur d’envoi. Consulter `/logs` avant de renvoyer volontairement `/scan` après une interruption.

`/favoris` ne voit pas les changements Chrome non publiés et ne rafraîchit pas les prix. Pour actualiser, utiliser `/scan`, attendre sa fin puis `/favoris`, en complément du scan automatique horaire.

Les workflows de commandes et de scanner partagent `uniqlo-monitor` pour protéger l’historique. Le curseur de commandes est chiffré séparément dans `monitor-data:data/telegram-commands.enc.json`. Ne pas faire tourner un lecteur getUpdates en parallèle du webhook. Un doublon de réponse reste possible après interruption entre envoi et sauvegarde.

## Maintenance Cloudflare et futures commandes

[Guide Worker](../telegram-webhook/README.md) : emplacements des secrets/variables, diagnostic en lecture seule depuis iPhone, mises à jour et retour arrière. Aucun secret dans le chat. La configuration fonctionne déjà ; le diagnostic **Configurer Cloudflare sans scan** en `verify_only=true` ne demande ni vrai scan ni message de test.

Toute commande future exige **catalogue partagé `commands.json` + routage Cloudflare + traitement + tests + documentation + déploiement Worker**. Une modification uniquement dans GitHub est incomplète. [Contrat complet](TELEGRAM_COMMANDS.md).
