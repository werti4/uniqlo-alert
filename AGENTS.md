# UNIQLO Alert — règles de reprise

Lire [docs/CODEX_HANDOFF.md](docs/CODEX_HANDOFF.md), [docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md), puis [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) et les fichiers concernés depuis la dernière `main`. [docs/HISTORY.md](docs/HISTORY.md) est une archive, pas une liste de blocages actuels.

**Cloudflare/Telegram opérationnels depuis le 29/10/2026 : webhook confirmé, premier scan naturel de 13:17 Paris validé, anciens calendriers GitHub retirés. `HOURLY_SCAN_ENABLED=true`, `SETUP_ENABLED=false`, `HOURLY_VERIFY_ENABLED=false`. Ne recréer ni Worker ni secrets, ne pas relancer l’activation sur la base des anciens échecs de format.**

**Toute commande Telegram actuelle ou future exige catalogue `telegram-webhook/commands.json` + routage Cloudflare + traitement + tests + documentation + déploiement Worker.** Lire [docs/TELEGRAM_COMMANDS.md](docs/TELEGRAM_COMMANDS.md). Une commande seulement ajoutée à Python/Actions est incomplète. GitHub exécute les travaux longs, déclenchés automatiquement ; aucune action manuelle utilisateur normalement requise.

Utilisateur sur iPhone : outils connectés et étapes adaptées à Safari, aucun terminal imposé ni secret demandé dans le chat. Aucun scan forcé ou message de test sans demande explicite. Préserver les favoris publiés depuis Chrome pendant le travail : récupérer main avant publication, sans forcer.

Le code et les résultats vérifiés priment sur un ancien message de conversation.

- Outil personnel gratuit : extension Chrome Manifest V3, UNIQLO France, EUR.
- L'extension gère les favoris. Tous les scans automatiques tournent sur GitHub Actions.
- Chaque baisse depuis le dernier prix valide crée une alerte. Telegram est activé ; un futur envoi de baisse reçu sur l’iPhone reste une preuve distincte des succès de commandes et du test antérieur. Telegram ne bloque pas les relevés. L’objectif facultatif ne filtre aucune baisse.
- Le premier relevé constitue la référence et ne déclenche pas d'alerte.
- Couleur et taille sont des préférences. Ne pas promettre de stock ni de prix précis par variante sans source vérifiée.
- En cas de page invalide, blocage ou erreur réseau : conserver le prix valide, afficher l'erreur et ralentir. Aucun contournement des protections.
- Ne jamais commiter de jeton, de clé, de favoris en clair ou de fichier privé. Les données distantes sont chiffrées.
- Ne pas annoncer la surveillance active sur la seule présence d'un jeton ou d'un workflow vert : vérifier un relevé réussi et l'envoi Telegram.
- Ne pas recréer le dépôt ou repartir d'un prototype si une version plus récente existe ici.
- Pour la fenêtre compacte, la CSP ou le paquet, exécuter aussi `tools/check_quick_ui.cjs` selon `docs/DEVELOPMENT.md` ; ne pas confondre API simulées et extension réellement installée.
- Préserver les données chiffrées publiées entre deux tâches ; vérifier l’état distant avant de conclure qu’une configuration manque.
- Valider les changements applicatifs avec `python3 -m unittest discover -s tests -p 'test_*.py'` et `npm test`.
- Mettre à jour `docs/PROJECT_CONTEXT.md` après une décision structurante ou une vérification effective. Indiquer les étapes manuelles restantes.
- Éviter les relances identiques : après un échec, lire l'erreur et changer l'action ou signaler précisément le blocage.
