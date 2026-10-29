# UNIQLO Alert — règles de reprise

Lire `docs/PROJECT_CONTEXT.md`, puis les fichiers concernés avant de modifier le projet.
Le code et les résultats vérifiés priment sur un ancien message de conversation.

- Outil personnel gratuit : extension Chrome Manifest V3, UNIQLO France, EUR.
- L'extension gère les favoris. Tous les scans automatiques tournent sur GitHub Actions.
- Chaque baisse depuis le dernier prix valide déclenche une alerte Telegram ; l'objectif facultatif ne filtre aucune baisse.
- Le premier relevé constitue la référence et ne déclenche pas d'alerte.
- Couleur et taille sont des préférences. Ne pas promettre de stock ni de prix précis par variante sans source vérifiée.
- En cas de page invalide, blocage ou erreur réseau : conserver le prix valide, afficher l'erreur et ralentir. Aucun contournement des protections.
- Ne jamais commiter de jeton, de clé, de favoris en clair ou de fichier privé. Les données distantes sont chiffrées.
- Ne pas annoncer la surveillance active sur la seule présence d'un jeton ou d'un workflow vert : vérifier un relevé réussi et l'envoi Telegram.
- Ne pas recréer le dépôt ou repartir d'un prototype si une version plus récente existe ici.
- Valider avec `python3 -m unittest discover -s tests -p 'test_*.py'` et `npm test`.
- Mettre à jour `docs/PROJECT_CONTEXT.md` après une décision structurante ou une vérification effective. Indiquer les étapes manuelles restantes.
- Éviter les relances identiques : après un échec, lire l'erreur et changer l'action ou signaler précisément le blocage.
