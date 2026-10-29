# UNIQLO Alert — règles de reprise

Lire `docs/PROJECT_CONTEXT.md`, puis `docs/DEVELOPMENT.md` et les fichiers concernés avant de modifier le projet.
`docs/HISTORY.md` est une archive : ne pas appliquer ses anciens blocages comme état courant.
Le code et les résultats vérifiés priment sur un ancien message de conversation.

- Outil personnel gratuit : extension Chrome Manifest V3, UNIQLO France, EUR.
- L'extension gère les favoris. Tous les scans automatiques tournent sur GitHub Actions.
- Chaque baisse depuis le dernier prix valide crée une alerte ; sa livraison Telegram nécessite une activation explicite. Telegram est reporté par l’utilisateur et ne bloque pas les relevés. L’objectif facultatif ne filtre aucune baisse.
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
