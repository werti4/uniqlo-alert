# Contrat des commandes Telegram — Cloudflare obligatoire

Décision utilisateur du 29 octobre 2026 : **toutes les commandes Telegram, actuelles et futures, doivent passer par Cloudflare**. Cette règle prime sur les anciens exemples de polling ou de lancement manuel d’Actions. Le Worker est déployé depuis le 29 octobre 2026 ; les cinq secrets Worker sont désormais présents, accès et webhook confirmés, premier dispatch horaire naturel validé. Voir PROJECT_CONTEXT.md et le guide Cloudflare pour l’état vérifié.

## Source de vérité unique

Le catalogue exécutable est [telegram-webhook/commands.json](../telegram-webhook/commands.json), chargé par Cloudflare via `commands.mjs` et par l’exécutant Python. Ne pas maintenir une deuxième liste de noms dans un script, un workflow ou un écran. Un traitement absent fait échouer le chargement Python et les tests : une commande ne doit pas être silencieusement oubliée du Worker.

| Commande | Entrée, autorisation et accusé de réception | Travail demandé et résultat |
| --- | --- | --- |
| `/logs` | Cloudflare, conversation privée/propriétaire et header secret Telegram | Diagnostic préparé par l’exécutant GitHub et envoyé dans la conversation privée |
| `/scan` | Cloudflare, même contrôle d’accès | Cloudflare demande le traitement ; GitHub effectue le scan long, annonce son début/sa fin et fournit les promotions ou un résultat incomplet explicite |
| `/favoris` | Cloudflare, même contrôle d’accès et accusé spécifique | Tous les favoris publiés, actifs et pausés, derniers prix connus, pastille 🔴 si promotion au dernier relevé, prix de base/date/erreurs et pagination ; aucun scan |

Les suffixes `/commande@NomDuBot` sont vérifiés. Les commandes absentes du catalogue et les messages non autorisés sont refusés. Les noms d’articles ne sont pas copiés dans le diagnostic /logs ; ils sont autorisés dans le bilan privé /scan explicitement demandé.

**« Commande gérée dans Cloudflare » signifie : réception immédiate, reconnaissance, autorisation, routage et file persistante dans Cloudflare.** Cela ne signifie pas que la lecture UNIQLO ou tous les calculs se font dans le Worker. GitHub reste un exécutant technique déclenché automatiquement par Cloudflare ; l’utilisateur ne doit pas avoir à ouvrir Actions pour lancer une commande. Le résultat final d’un travail GitHub peut attendre un runner. Aucune clé de déchiffrement des favoris n’est confiée au Worker dans cette architecture.

## Chemin normal après déploiement

Telegram → webhook Cloudflare → catalogue partagé → contrôles d’accès → file persistante/accusé → déclenchement automatique de l’exécutant → résultat Telegram.

Le cron horaire Cloudflare est séparé des commandes : il demande un scan à :17 de chaque heure lorsque HOURLY_SCAN_ENABLED vaut true. Les erreurs, pauses UNIQLO, quotas et délais externes restent applicables.

Le polling getUpdates conservé dans Python est uniquement un mode de transition/retour arrière. Ce n’est pas la cible des nouvelles fonctionnalités. Ne pas créer de nouvelle commande uniquement dans ce fallback ou demander à l’utilisateur de lancer un workflow pour l’utiliser normalement.

## Ajouter une commande : travail complet obligatoire

1. Ajouter son nom, sa description, son accusé et son identifiant de traitement au catalogue partagé.
2. Définir son comportement dans le Worker : authentification, paramètres éventuels, réponse et routage. Une nouvelle commande courte peut être traitée directement dans Cloudflare ; un travail long peut être délégué automatiquement à un exécutant.
3. Si un traitement Python est utilisé, l’implémenter et l’enregistrer. Le catalogue ne crée pas une fonction à lui seul. Ne pas assouplir une validation pour faire passer un traitement absent.
4. Tester tous les noms du catalogue, les suffixes, le refus des inconnus/hors propriétaire, la confidentialité, les erreurs et les risques de répétition. Vérifier le résultat de la commande et la persistance si elle modifie un état.
5. Mettre à jour ce tableau, SETUP.md, PROJECT_CONTEXT.md et les preuves de VALIDATION.md. Si le menu Telegram des commandes est configuré, le synchroniser avec le catalogue ; ne pas considérer le menu comme l’implémentation.
6. Publier le code, vérifier la CI et **redéployer le Worker**. Un commit sur GitHub ne met pas à jour un service Cloudflare déjà déployé, sauf pipeline de déploiement explicitement configuré et vérifié.
7. Confirmer une commande réelle depuis Telegram avant de la déclarer active. Pour /scan ou toute action avec effets, respecter l’autorisation utilisateur : aucun scan réel forcé pendant les tests de développement.

## État actuel et passage de relais

Catalogue : /logs, /scan et /favoris. Tests locaux du code courant : 63 Python et 27 Node réussis avec services simulés. Assemblage Worker à vérifier avec Wrangler --dry-run après modification de ses imports. Déploiement initial effectué ; secrets Cloudflare présents (noms/types vérifiés), validité, liaison Actions, webhook et premier horaire naturel confirmés ; réception réelle sur iPhone à observer sans message de test forcé. Lire aussi [CODEX_HANDOFF.md](CODEX_HANDOFF.md). Pour reprendre dans une autre conversation, lire AGENTS.md, PROJECT_CONTEXT.md, ce contrat et telegram-webhook/README.md. Ne pas repartir d’un ancien ZIP ou recréer les identifiants déjà fonctionnels.
