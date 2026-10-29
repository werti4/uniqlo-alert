"""Send an explicitly requested setup message to a private Telegram chat.

No product access, no encryption key, no mutation of monitoring state.
Never print request URLs, API responses, tokens or chat identifiers.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request


class SetupError(RuntimeError):
    pass


def api(token, method, payload):
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        messages = {
            400: "Conversation introuvable ou requête refusée. Vérifiez TELEGRAM_CHAT_ID et démarrez le bot.",
            401: "Jeton refusé. Vérifiez le secret TELEGRAM_BOT_TOKEN.",
            403: "Accès refusé. Débloquez le bot et appuyez sur Démarrer dans Telegram.",
            429: "Telegram demande une pause. Attendez avant de relancer le test.",
        }
        raise SetupError(messages.get(error.code, "Telegram indisponible. Réessayez plus tard.")) from None
    except (urllib.error.URLError, TimeoutError, ValueError):
        raise SetupError("Telegram inaccessible ou réponse invalide. Aucun identifiant affiché.") from None
    if not isinstance(result, dict) or result.get("ok") is not True or not isinstance(result.get("result"), dict):
        raise SetupError("Telegram n’a pas confirmé la requête.")
    return result["result"]


def check(token, chat_id):
    token, chat_id = token.strip(), chat_id.strip()
    if not re.fullmatch(r"\d+:[A-Za-z0-9_-]+", token):
        raise SetupError("Secret TELEGRAM_BOT_TOKEN absent ou format invalide.")
    if not re.fullmatch(r"[1-9]\d*", chat_id):
        raise SetupError("Secret TELEGRAM_CHAT_ID absent ou invalide : utilisez l’identifiant numérique de votre conversation privée.")
    bot = api(token, "getMe", {})
    if bot.get("is_bot") is not True:
        raise SetupError("L’identité du bot n’a pas été confirmée.")
    chat = api(token, "getChat", {"chat_id": chat_id})
    if chat.get("type") != "private" or str(chat.get("id")) != chat_id:
        raise SetupError("Le test est réservé à votre conversation privée avec le bot.")
    result = api(token, "sendMessage", {
        "chat_id": chat_id,
        "text": "✅ UNIQLO Alert — message de test\n\nLa liaison GitHub Actions → Telegram fonctionne.\nCe message ne correspond à aucune baisse de prix.\n\nAprès réception sur votre iPhone, activez UA_TELEGRAM_ENABLED=true dans les variables Actions pour recevoir les alertes automatiques.",
        "link_preview_options": {"is_disabled": True},
    })
    if not isinstance(result.get("message_id"), int) or str(result.get("chat", {}).get("id")) != chat_id:
        raise SetupError("Confirmation d’envoi Telegram incomplète. Vérifiez votre conversation avant de relancer.")


def main():
    try:
        check(os.getenv("TELEGRAM_BOT_TOKEN", ""), os.getenv("TELEGRAM_CHAT_ID", ""))
    except SetupError as error:
        print(str(error), file=sys.stderr)
        return 1
    except Exception:
        print("Test Telegram interrompu. Aucun identifiant affiché.", file=sys.stderr)
        return 1
    print("Telegram a confirmé l’envoi du message de test. Confirmez sa réception sur votre iPhone ; les alertes de prix n’ont pas été modifiées.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
