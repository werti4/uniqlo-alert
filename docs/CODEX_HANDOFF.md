# Reprise Codex — configuration opérationnelle

Lire la dernière `main`, [AGENTS.md](../AGENTS.md), [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md), puis les fichiers concernés. **Ne pas recommencer l’activation : aucun blocage de configuration connu.** Les anciens échecs de secret sont résolus et archivés.

## État au 29 octobre 2026, Europe/Paris

- Worker existant : **uniqlo-telegram-webhook**, https://uniqlo-telegram-webhook.uniqlo-alert-werti4.workers.dev ; webhook `/telegram` enregistré et confirmé.
- DO SQLite `INBOX` → `TelegramInbox`, migration `v1`. Cinq secrets requis fonctionnels ; secret supplémentaire Cloudflare inutilisé préservé. Noms/emplacements dans le contexte, jamais de valeurs.
- Cron Cloudflare `17 * * * *`, `HOURLY_SCAN_ENABLED=true`, `HOURLY_VERIFY_ENABLED=false`, `SETUP_ENABLED=false`, également dans wrangler.jsonc.
- Actions reçoit les commandes automatiquement ; `UA_TELEGRAM_WEBHOOK_URL`, secret commun, identité Telegram et `UA_TELEGRAM_ENABLED=true` validés. Aucun getUpdates en parallèle.
- Premier scan naturel **13:17 Paris**, [40872057387](https://github.com/werti4/uniqlo-alert/actions/runs/40872057387), et diagnostic [40872060775](https://github.com/werti4/uniqlo-alert/actions/runs/40872060775) réussis. Calendriers GitHub retirés ensuite dans `5fdd32a`, workflows/dispatchs et publications de favoris conservés.
- Deux autres runs de commandes réussis à 13:28 et 13:34 Paris ; utilisateur : « Tout a l’air de bien marcher ». [Preuves et limites](VALIDATION.md).

## Règles de continuité

Toutes les commandes actuelles/futures passent par Cloudflare : **catalogue `commands.json` + routage + traitement + tests + documentation + déploiement Worker**. Un commit GitHub seul ne déploie pas Cloudflare. [Contrat](TELEGRAM_COMMANDS.md) : `/logs` diagnostic, `/scan` actualisation explicite/progressions/promotions, `/favoris` derniers prix datés et 🔴, **sans scan**.

Utilisateur sur iPhone : outils connectés d’abord, étapes Safari si intervention nécessaire, aucun terminal imposé ni secret dans le chat. Aucun scan forcé ou message de test sans demande explicite. Un contrôle administratif autorisé peut utiliser **Configurer Cloudflare sans scan** en `verify_only=true` ; `/configure` reste fermé. Aucun suivi ponctuel supplémentaire actif.

Préserver Chrome, réglages, favoris et clé. `UA_ENCRYPTION_KEY` uniquement Chrome/Actions. Ne recréer ni Worker, ni secrets, ni dépôt ; ne pas déchiffrer les favoris pour vérifier une configuration. Récupérer main avant publication, ne pas écraser une publication Chrome concurrente ; ne pas fusionner `monitor-data` dans main.

Dernières suites applicatives : **68 Python / 33 Node**, simulations ; détails dans VALIDATION.md. Pour un changement documentaire, contrôler seulement cohérence/liens/diff. Pour l’applicatif, suivre [DEVELOPMENT.md](DEVELOPMENT.md). Publication possible via connecteur GitHub avec SHA attendu ; capacités/outils et chemins locaux à revérifier à la reprise.

## Ce qui reste à surveiller

Dates/erreurs réelles par article et future livraison d’une véritable alerte de baisse sur iPhone. Aucun succès futur garanti. Offres gratuites avec quotas, Billing non lisible via OAuth ; aucun abonnement modifié. [Maintenance, contrôle iPhone et retour arrière](../telegram-webhook/README.md). Conserver la file DO et les données lors d’un retour arrière, jamais polling et webhook simultanés.
