# UNIQLO Alert

Une extension Chrome pour gérer ses favoris UNIQLO France, suivre leur prix et recevoir les baisses sur Telegram sur iPhone. Le scanner fonctionne sur GitHub Actions, même lorsque le PC est éteint.

## Fonctionnalités

- Tableau de bord : photos, nom, référence, prix, réduction affichée, historique et plus bas observé.
- Jusqu'à 50 favoris : ajout depuis une fiche ouverte ou son URL, recherche, tri, pause et suppression.
- Chaque baisse de prix détectée après le premier relevé produit une alerte ; aucun seuil minimum. Un objectif de prix facultatif permet de repérer les baisses qui atteignent son budget.
- Alertes Telegram avec ancien prix, nouveau prix et lien vers la fiche. Les envois qui échouent restent en attente.
- Synchronisation explicite des favoris chiffrés avec GitHub, protection contre l'écrasement des modifications d'un autre appareil.
- État de la surveillance : dernière lecture valide, erreur éventuelle et données devenues anciennes.

Les couleurs et tailles souhaitées sont des préférences. Le scanner vérifie le groupe de prix de la fiche ; il ne vérifie pas le stock de la combinaison couleur/taille.

## État et installation

Le code, les tests et les workflows sont publiés. L’installation et la configuration sont propres à chaque utilisateur : jeton limité au dépôt dans Chrome, même clé dans Chrome et le secret Actions, puis favoris publiés. **Telegram est facultatif et peut être configuré plus tard.** L’état vérifié de ce projet est consigné dans [le contexte de référence](docs/PROJECT_CONTEXT.md). Un workflow qui ignore le scan faute de configuration ne constitue pas un relevé réussi.

1. Ouvrir l'onglet [Actions](https://github.com/werti4/uniqlo-alert/actions) et la dernière exécution réussie de **Vérifier le projet**.
2. Télécharger l'artefact `uniqlo-alert-extension` et le décompresser. S'il contient un second fichier `uniqlo-alert-extension.zip`, le décompresser également. Ouvrir `chrome://extensions`.
3. Activer le mode développeur et choisir **Charger l'extension non empaquetée**, en sélectionnant le dossier qui contient `manifest.json`.
4. Cliquer sur l'extension et suivre [le guide de configuration](docs/SETUP.md).

L'installation locale évite les frais de publication dans le Chrome Web Store. Le paquet ne contient aucun identifiant personnel.

## Fréquence et fiabilité

La cible est un scan horaire demandé par Cloudflare à `:17`. Le Worker est déployé ; ses secrets, le webhook et le switch horaire restent à activer selon [le guide Cloudflare](telegram-webhook/README.md). Pendant cette transition, l’ancien calendrier GitHub toutes les **5 minutes** reste publié. GitHub peut retarder ou omettre un lancement. Le scan parcourt les favoris progressivement : la fraîcheur réelle est indiquée par article. En cas de limite UNIQLO, les scans se mettent en attente plutôt que d'insister.

Cette configuration est un compromis initial à mesurer. Elle n'offre ni temps réel garanti, ni garantie contre les blocages. Une page ou les données UNIQLO peuvent changer ; une lecture invalide conserve le dernier prix connu et n'est jamais interprétée comme une promotion ou une rupture.

Le premier relevé ne génère pas d'alerte. Un article déjà en promotion lors de son ajout ne produit une alerte que si son prix observé baisse ensuite. La réduction entre prix de base et prix promotionnel reste visible dans le tableau de bord.

## Gratuité et confidentialité

- Dépôt public et runners Linux standard GitHub Actions ; aucun service payant ou serveur personnel nécessaire. Les conditions et quotas des services peuvent évoluer.
- Favoris chiffrés dans `data/watchlist.enc.json` sur la branche principale ; relevés chiffrés dans `data/state.enc.json` sur `monitor-data`.
- AES-256-GCM, clé partagée entre l'extension et le secret Actions `UA_ENCRYPTION_KEY`. Les jetons Telegram restent dans les secrets Actions.
- Le jeton GitHub et la clé sont conservés localement par Chrome. Ce stockage n'est pas un coffre-fort matériel ; protéger le profil de navigateur et sauvegarder la clé séparément.
- Le dépôt public expose le code et les métadonnées des commits/exécutions. Le chiffrement protège le contenu des favoris, pas l'existence ni la taille des mises à jour.
- Les exports volontaires des favoris sont en clair et ne contiennent aucun jeton.

## Organisation

| Chemin | Rôle |
| --- | --- |
| `extension/` | Extension et interface, sans bibliothèque externe |
| `scanner/monitor.py` | Lecture UNIQLO, historique chiffré, file Telegram |
| `.github/workflows/scan.yml` | Planification et exécution du scanner |
| `.github/workflows/check.yml` | Tests et paquet installable |
| `tools/generate_icons.py` | Restauration des icônes PNG depuis leurs sources texte |
| `tests/` | Régressions Python, JavaScript et compatibilité du chiffrement |
| `docs/PROJECT_CONTEXT.md` | Périmètre, décisions et point de reprise |
| `docs/SETUP.md` | Installation, secrets et dépannage |
| `docs/DEVELOPMENT.md` | Fichiers à modifier, tests et livraison |
| `docs/VALIDATION.md` | Preuves récentes et limites |
| `docs/HISTORY.md` | Anciennes étapes archivées |

## Validation locale

Avec Python 3.12 et Node.js 22 ou plus récent :

```sh
python3 -m pip install -r requirements.txt
python3 tools/generate_icons.py
python3 -m unittest discover -s tests -p 'test_*.py'
npm test
```

Les tests utilisent des données synthétiques et ne scannent pas UNIQLO. Les tests JavaScript de compatibilité lancent `python3`, qui doit disposer de `cryptography`. Les icônes PNG sont générées à l'identique par CI ; exécuter aussi le générateur avant une installation directement depuis les sources.

## Limites connues

- Ni achat automatique ni connexion au compte UNIQLO.
- Pas de garantie de stock, d'avantage membre ou de réduction à appliquer au panier.
- Les notifications dépendent du bon fonctionnement de GitHub, UNIQLO, Telegram et des réglages de notifications de l'iPhone.
- Un arrêt brutal juste après l'envoi Telegram mais avant sa sauvegarde peut produire un doublon au réessai ; `sendMessage` ne fournit pas de garantie exactement une fois.
- GitHub peut désactiver les scans planifiés d'un dépôt public après 60 jours sans activité. Vérifier régulièrement Actions ; aucun mécanisme ne crée artificiellement de l'activité.

Outil personnel indépendant, sans affiliation avec UNIQLO.
