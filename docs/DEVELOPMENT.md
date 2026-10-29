# Modifier UNIQLO Alert sans perdre le contexte

Lire d’abord [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md), puis l’état Git et les fichiers concernés. L’historique archivé n’est pas une liste d’actions à répéter. Utiliser le checkout existant ; chaque tâche cloud est déjà isolée, pas de worktree sauf demande explicite.

## Où intervenir

| Changement demandé | Fichiers principaux | Contrôles associés |
| --- | --- | --- |
| Petite fenêtre automatique et popup Chrome | `extension/quick.js`, `quick.html`, `quick-popup.css` | Test navigateur sous CSP, dimensions, ajout/retrait, réduction/réouverture |
| Tableau de bord, recherche, tri, détails | `extension/app.html`, `app.css`, `app.js` | Tests JS et vérification visuelle ; prix manquants et erreurs |
| Stockage local, messages, publication/synchronisation GitHub | `extension/background.js` | Tests JS de concurrence, conflits et accès ; aucun secret dans le résumé exposé au site |
| URLs, prix affichés, validation, chiffrement JS | `extension/core.js` | Tests JS + tests d’interopérabilité Python |
| Lecture UNIQLO, prix, historique, pauses, Telegram | `scanner/monitor.py` | Tests Python + interopérabilité si format modifié ; une lecture réelle autorisée reste une validation distincte |
| Fréquence, secrets Actions, permissions, déclencheurs | `.github/workflows/scan.yml` | Scripts Python embarqués et prérequis ; vérifier les étapes réellement exécutées et les résultats du scan |
| Commandes privées Telegram | `tools/telegram_commands.py`, `tools/telegram_scan.py`, `.github/workflows/telegram-commands.yml`, `tests/test_telegram_commands.py`, `tests/test_telegram_scan.py` | Autorisation propriétaire, /logs en lecture seule, /scan uniquement sur demande explicite, curseur séparé, groupe uniqlo-monitor partagé |
| Diagnostic Telegram sans scan de prix | `.github/workflows/test-telegram.yml`, `tools/telegram_check.py`, `tests/test_telegram_check.py` | Test manuel uniquement, conversation privée et absence de secrets dans les erreurs |
| Tests, génération et paquet téléchargeable | `.github/workflows/check.yml`, `tools/` | CI complète et contenu de l’artefact |
| Permissions, injection sur UNIQLO, version | `extension/manifest.json` | Périmètre minimal, CSP préservée et test navigateur |

## Développer et vérifier

Depuis la racine du checkout, avec Python 3.12 et Node.js >=22 :

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --disable-pip-version-check -r requirements.txt
python3 -m unittest discover -s tests -p 'test_*.py'
npm test
python3 tools/generate_icons.py
```

La CI utilise Python 3.12 et Node.js 22 ; les validations cloud précédentes utilisaient Node.js 24. Les tests JS de chiffrement démarrent `python3` : activer `.venv` dans le même terminal. Aucun `npm install` nécessaire pour l’extension et ses tests Node standards.

Pour une modification de la fenêtre compacte, de sa CSP ou du paquet, lancer aussi le test navigateur comme la CI :

```sh
npm install --prefix /tmp/uniqlo-ui-test --no-package-lock --no-save playwright@1.62.1
/tmp/uniqlo-ui-test/node_modules/.bin/playwright install --with-deps chromium
PLAYWRIGHT_MODULE=/tmp/uniqlo-ui-test/node_modules/playwright node tools/check_quick_ui.cjs
```

Si Playwright et Chromium sont déjà installés, sélectionner leurs chemins avec `PLAYWRIGHT_MODULE` et `CHROMIUM_EXECUTABLE` au lieu de réinstaller. Dans le cloud préparé, ces chemins étaient respectivement `/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright` et `/usr/lib/chromium/chromium` ; vérifier leur existence avant utilisation. Les captures vont dans `test-results/quick-ui/`, ignoré par Git.

Le test navigateur sert le vrai HTML avec la CSP du manifeste, contrôle largeur 360 px, styles, grille et interactions. Ses API Chrome et pages UNIQLO sont simulées. Il ne prouve ni une installation réelle ni une collecte UNIQLO. Les seuls changements documentaires se vérifient par cohérence, liens et `git diff --check` ; ils ne nécessitent pas de relancer les tests applicatifs.

## Points à ne pas casser

- CSP : `style-src 'self'`. Pas de `<style>` inline dans le popup. Dimensions dans `quick-popup.css`, styles du Shadow DOM via `CSSStyleSheet` construit. Ne pas ajouter `unsafe-inline` pour masquer une régression.
- Scripts de contenu : seuls résumé restreint, bascule du favori courant et ouverture du tableau de bord sont autorisés. L’URL de l’émetteur fait foi. Aucun accès aux jetons, clés ou commandes privilégiées.
- Favoris : sérialisation des mutations, limite de 50, détection des conflits de révision, publication explicite, pas d’effacement lors d’un échec réseau/déchiffrement.
- Chiffrement : compatibilité Chrome/Python, AAD et schémas conservés. Ne pas régénérer de clé ni réinitialiser l’historique pour contourner un échec.
- Prix : groupe produit exact, EUR, dernier prix valide conservé. Premier relevé sans alerte ; toute baisse ultérieure compte, objectif atteint ou non.
- Scanner : robots.txt, espacement des requêtes, budget de durée, délai d’attente et pauses conservés. Pas de scan massif ni contournement.
- Actions : exécution sur branche par défaut, groupe `uniqlo-monitor`, `cancel-in-progress: false`, permission d’écriture limitée au job scanner. Un workflow vert avec une étape `skipped` n’est pas un relevé réussi.

## Livrer une modification

1. Vérifier les changements existants et la branche distante avant de modifier ou publier. Les favoris chiffrés peuvent avoir été publiés depuis Chrome entre deux tâches ; intégrer les nouveautés sans écraser de données. Préserver les fichiers locaux existants.
2. Tester le comportement concerné et lancer les vérifications requises par `AGENTS.md`. Indiquer résultats et limites réels, sans convertir un test simulé en preuve de fonctionnement personnel.
3. Si le paquet Chrome change, incrémenter la version du manifeste. Pour chaque nouvel asset, mettre à jour **les deux listes** de `check.yml` : génération ZIP et fichiers transmis à `upload-artifact`.
4. Le paquet public contient actuellement **13 fichiers** : manifeste, tableau de bord (HTML/CSS/JS), `core.js`, `background.js`, `quick.html`, `quick.js`, `quick-popup.css`, quatre icônes. Aucun `demo.js`, bootstrap privé, favori en clair ou secret. L’artefact GitHub contient directement les fichiers, sans ZIP imbriqué.
5. Publier selon la demande et l’autorisation de la tâche ; les changements de code des étapes précédentes ont été publiés sur `main`. Vérifier le push et l’exécution CI correspondant au commit. Une CI réussie ne prouve pas que la version est installée chez l’utilisateur.
6. Mettre à jour le contexte courant, les preuves de validation et les étapes manuelles restantes. Ajouter l’historique utile dans `HISTORY.md` plutôt qu’une succession de paragraphes contradictoires dans le contexte courant.

Pour installer une mise à jour, remplacer les fichiers dans le dossier déjà chargé, cliquer **Actualiser** dans `chrome://extensions` et recharger les pages UNIQLO. Éviter la désinstallation pour conserver stockage local, favoris et réglages. Les artefacts expirent après 7 jours ; obtenir le paquet d’une exécution récente réussie, pas d’un ancien lien supposé permanent.
