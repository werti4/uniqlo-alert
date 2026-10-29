"""UNIQLO France: public product pages, encrypted state, Telegram outbox."""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = "https://www.uniqlo.com"
AGENT = "UniqloAlertPersonal/1.0"
AAD = b"uniqlo-alert:v1"
MAX_BYTES = 8_000_000
REQUEST_TIMEOUT = 8
SCAN_BUDGET_SECONDS = 300
REQUEST_GAP_SECONDS = 2
MAX_TELEGRAM_PER_RUN = 50
TELEGRAM_BUDGET_SECONDS = 60


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def b64(data):
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def unb64(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def aes_key(value):
    key = unb64(value)
    if len(key) != 32:
        raise ValueError("Une clé AES-256 de 32 octets est requise")
    return key


def encrypt(value, key):
    nonce = os.urandom(12)
    payload = AESGCM(aes_key(key)).encrypt(nonce, json.dumps(value, ensure_ascii=False).encode(), AAD)
    return {"v": 1, "alg": "A256GCM", "iv": b64(nonce), "data": b64(payload)}


def decrypt(value, key):
    if not isinstance(value, dict) or value.get("v") != 1 or value.get("alg") != "A256GCM":
        raise ValueError("Format de chiffrement inconnu")
    nonce = unb64(value["iv"])
    if len(nonce) != 12:
        raise ValueError("Nonce de chiffrement invalide")
    return json.loads(AESGCM(aes_key(key)).decrypt(nonce, unb64(value["data"]), AAD))


def canonical_url(raw):
    u = urllib.parse.urlsplit(raw)
    match = re.fullmatch(r"/fr/fr/products/(E\d{6}-\d{3})/(\d{2})/?", u.path)
    if u.scheme != "https" or u.netloc != "www.uniqlo.com" or not match:
        raise ValueError("Une fiche produit UNIQLO France HTTPS est requise")
    return ROOT + u.path.rstrip("/"), f"{match[1]}-{match[2]}"


def cents(value):
    if isinstance(value, bool):
        raise ValueError("Prix EUR absent ou invalide")
    try:
        p = Decimal(str(value).replace(",", "."))
        if p.is_finite() and 0 < p < 100000 and p * 100 == (p * 100).to_integral():
            return int(p * 100)
    except (InvalidOperation, ValueError):
        pass
    raise ValueError("Prix EUR absent ou invalide")


def object_data(value):
    return value if isinstance(value, dict) else {}


def parse_product(document, expected_id):
    """Parse JSON only. Never execute website scripts or mix price groups."""
    marker = re.search(r"window\.__PRELOADED_STATE__\s*=\s*", document)
    if not marker:
        raise ValueError("Données produit absentes de la page")
    state = json.JSONDecoder().raw_decode(document[marker.end():])[0]
    entities = object_data(object_data(state).get("entity"))
    entry = object_data(entities.get("pdpEntity")).get(expected_id)
    if not entry or not isinstance(entry.get("product"), dict):
        raise ValueError("Référence produit différente ou indisponible")
    p = entry["product"]
    if f"{p.get('productId')}-{p.get('priceGroup')}" != expected_id:
        raise ValueError("Groupe de prix différent")
    prices = object_data(p.get("prices"))
    promo, base = prices.get("promo"), prices.get("base")
    selected = promo if isinstance(promo, dict) and promo.get("value") is not None else base
    if not isinstance(selected, dict) or object_data(selected.get("currency")).get("code") != "EUR":
        raise ValueError("Prix EUR indisponible")
    current = cents(selected.get("value"))
    regular = None
    if isinstance(base, dict) and object_data(base.get("currency")).get("code") == "EUR":
        regular = cents(base.get("value"))
    if regular is not None and current > regular:
        raise ValueError("Prix promotionnel supérieur au prix de base ; lecture ambiguë")
    color = object_data(object_data(p.get("representative")).get("color")).get("displayCode")
    images = object_data(object_data(p.get("images")).get("main"))
    image_url = object_data(images.get(color)).get("image") if isinstance(color, str) else None
    if not image_url:
        image_url = next((entry.get("image") for entry in images.values() if isinstance(entry, dict) and entry.get("image")), None)
    if not isinstance(image_url, str) or not image_url.startswith("https://image.uniqlo.com/"):
        image_url = None
    colors = p.get("colors") if isinstance(p.get("colors"), list) else []
    sizes = p.get("sizes") if isinstance(p.get("sizes"), list) else []
    rating = object_data(p.get("rating"))
    average, count = rating.get("average"), rating.get("count")
    average = average if isinstance(average, (int, float)) and not isinstance(average, bool) and 0 <= average <= 5 else None
    count = count if isinstance(count, int) and not isinstance(count, bool) and count >= 0 else None
    return {
        "id": expected_id, "name": str(p.get("name", "Article UNIQLO"))[:200],
        "priceCents": current, "regularCents": regular, "currency": "EUR",
        "image": image_url, "colors": [{"code": c.get("displayCode"), "name": c.get("name")} for c in colors if isinstance(c, dict)],
        "sizes": [s.get("name") for s in sizes if isinstance(s, dict) and isinstance(s.get("name"), str)],
        "availability": None, "stockNote": "Tailles au catalogue ; stock par taille non vérifié",
        "priceScope": "product-price-group",
        "priceNote": "Prix du groupe produit ; prix et stock de votre taille/couleur non vérifiés",
        "rating": average, "reviewCount": count,
    }


class BlockedError(Exception):
    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after if isinstance(retry_after, int) and not isinstance(retry_after, bool) and retry_after >= 0 else None


class NetworkError(ValueError):
    pass


def retry_after_seconds(value, reference=None):
    """Parse Retry-After seconds or an HTTP date, without shortening a server delay."""
    if not value:
        return None
    try:
        if str(value).strip().isdigit():
            return int(str(value).strip())
        until = parsedate_to_datetime(str(value))
        if until.tzinfo is None:
            until = until.replace(tzinfo=dt.timezone.utc)
        return max(0, int((until - (reference or dt.datetime.now(dt.timezone.utc))).total_seconds()) + 1)
    except (ValueError, TypeError, OverflowError):
        return None


def timestamp(value):
    try:
        stamp = dt.datetime.fromisoformat(value)
        if stamp.tzinfo is None:
            raise ValueError("Date sans fuseau")
        return stamp
    except (ValueError, TypeError):
        return None


def after_delay(at, seconds):
    # The run start may be several minutes before the failing request.
    # Count Retry-After from the response, never from that older timestamp.
    reference = max(timestamp(at), timestamp(now()))
    try:
        return (reference + dt.timedelta(seconds=seconds)).isoformat(timespec="seconds")
    except OverflowError:
        return dt.datetime.max.replace(tzinfo=dt.timezone.utc).isoformat(timespec="seconds")


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        destination = urllib.parse.urlsplit(newurl)
        if destination.scheme != "https" or destination.netloc != "www.uniqlo.com":
            raise BlockedError("Redirection hors UNIQLO HTTPS refusée")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Robots:
    """Apply Allow/Disallow wildcard rules; prefer longest match and Allow ties."""
    def __init__(self, text):
        groups, agents, rules, directives = [], [], [], False
        for line in text.splitlines() + ["User-agent: __end__"]:
            line = line.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            k, v = [s.strip() for s in line.split(":", 1)]
            if k.lower() == "user-agent":
                if directives:
                    groups.append((agents, rules)); agents, rules, directives = [], [], False
                agents.append(v.lower())
            elif k.lower() in ("allow", "disallow"):
                directives = True
                if v:
                    rules.append((k.lower(), v))
        matches = [(max(len(a) if a != "*" else 0 for a in aa if a == "*" or a in AGENT.lower()), rr)
                   for aa, rr in groups if any(a == "*" or a in AGENT.lower() for a in aa)]
        longest = max((x[0] for x in matches), default=-1)
        self.rules = [rule for length, rr in matches if length == longest for rule in rr]

    def allowed(self, url):
        u = urllib.parse.urlsplit(url)
        path = u.path + ("?" + u.query if u.query else "")
        matches = []
        for kind, pattern in self.rules:
            regex = "^" + re.escape(pattern).replace(r"\*", ".*")
            if pattern.endswith("$"):
                regex = regex[:-2] + "$"
            if re.search(regex, path):
                matches.append((len(pattern.replace("*", "").rstrip("$")), kind == "allow"))
        return max(matches)[1] if matches else True


def get_page(url):
    req = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept-Language": "fr-FR,fr;q=0.9"})
    try:
        with urllib.request.build_opener(SafeRedirect).open(req, timeout=REQUEST_TIMEOUT) as response:
            if urllib.parse.urlsplit(response.geturl()).path.rstrip("/") != urllib.parse.urlsplit(url).path.rstrip("/"):
                raise ValueError("La fiche demandée redirige vers une autre page")
            content = response.read(MAX_BYTES + 1)
            if len(content) > MAX_BYTES:
                raise ValueError("Page trop volumineuse")
            return content.decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            raise BlockedError(f"UNIQLO limite l'accès (HTTP {e.code})", retry_after_seconds((e.headers or {}).get("Retry-After"))) from None
        if e.code in (500, 502, 503, 504):
            raise NetworkError(f"UNIQLO temporairement indisponible (HTTP {e.code})") from None
        raise ValueError(f"HTTP {e.code}") from None
    except (urllib.error.URLError, TimeoutError):
        raise NetworkError("Erreur réseau UNIQLO") from None


def observe(state, favorite, product, at):
    previous = state.setdefault("products", {}).get(favorite["id"], {})
    old_price = previous.get("priceCents")
    history = list(previous.get("history", []))
    if old_price != product["priceCents"]:
        history.append({"at": at, "priceCents": product["priceCents"]})
    item = {**product, "url": favorite["url"], "lastCheckedAt": at, "lastSuccessfulAt": at,
            "lastAttemptAt": at, "status": "ok", "history": history[-120:]}
    item["firstPriceCents"] = previous.get("firstPriceCents", product["priceCents"])
    item["lowestCents"] = min(previous.get("lowestCents", product["priceCents"]), product["priceCents"])
    state["products"][favorite["id"]] = item
    threshold = favorite.get("targetCents")
    if old_price is not None and product["priceCents"] < old_price:
        event_id = hashlib.sha256(f"{favorite['id']}:{at}:{old_price}:{product['priceCents']}".encode()).hexdigest()[:24]
        event = {"id": event_id, "productId": favorite["id"], "name": product["name"], "url": favorite["url"],
                 "at": at, "oldCents": old_price, "newCents": product["priceCents"], "delivery": "pending",
                 "targetReached": threshold is not None and product["priceCents"] <= threshold}
        state.setdefault("alerts", []).append(event)
    # Do not discard pending events even if delivery is temporarily unavailable.
    all_events = state.setdefault("alerts", [])
    state["alerts"] = [e for e in all_events if e["delivery"] == "pending"] + [e for e in all_events if e["delivery"] != "pending"][-100:]


class GitHubState:
    def __init__(self, token, repo, branch="monitor-data"):
        self.token, self.repo, self.branch, self.sha = token, repo, branch, None
        self.branch_ready = False

    def api(self, path, method="GET", data=None):
        req = urllib.request.Request("https://api.github.com/repos/" + self.repo + path,
              data=json.dumps(data).encode() if data is not None else None, method=method,
              headers={"Authorization": "Bearer " + self.token, "Accept": "application/vnd.github+json",
                       "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json", "User-Agent": AGENT})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise RuntimeError(f"GitHub HTTP {e.code}") from None

    def load(self, key):
        record = self.api("/contents/data/state.enc.json?ref=" + self.branch)
        if record is None:
            if self.api("/git/ref/heads/" + self.branch) is not None:
                raise RuntimeError("Historique absent d'une branche de données existante ; restauration requise")
            return {"schema": 1, "products": {}, "alerts": []}
        self.sha = record["sha"]
        self.branch_ready = True
        return decrypt(json.loads(base64.b64decode(record["content"])), key)

    def save(self, state, key):
        if not self.branch_ready:
            if self.api("/git/ref/heads/" + self.branch) is None:
                main = self.api("/git/ref/heads/" + os.getenv("DEFAULT_BRANCH", "main"))
                if not main:
                    raise RuntimeError("Branche principale introuvable")
                self.api("/git/refs", "POST", {"ref": "refs/heads/" + self.branch, "sha": main["object"]["sha"]})
            self.branch_ready = True
        payload = {"message": "monitor: encrypted snapshot [skip ci]", "branch": self.branch,
                   "content": base64.b64encode(json.dumps(encrypt(state, key)).encode()).decode()}
        if self.sha:
            payload["sha"] = self.sha
        response = self.api("/contents/data/state.enc.json", "PUT", payload)
        if not response:
            raise RuntimeError("Impossible de sauvegarder l'historique")
        self.sha = response["content"]["sha"]


class TelegramError(RuntimeError):
    def __init__(self, message="Envoi Telegram impossible", retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after if isinstance(retry_after, int) and not isinstance(retry_after, bool) and retry_after >= 0 else None


def telegram_send(event, token, chat_id):
    old, new = event["oldCents"] / 100, event["newCents"] / 100
    pct = round(100 * (old - new) / old)
    message = (f"📉 <b>Baisse de prix UNIQLO</b>\n\n<b>{html.escape(event['name'])}</b>\n"
               f"{old:.2f} € → <b>{new:.2f} €</b> (−{pct} %)\n"
               "\nStock par taille à vérifier sur la fiche.\n")
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", method="POST",
        data=json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "HTML",
          "link_preview_options": {"is_disabled": True},
          "reply_markup": {"inline_keyboard": [[{"text": "Voir l'article ↗", "url": event["url"]}]]}}).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.load(r)
            if not result.get("ok"):
                raise TelegramError(retry_after=result.get("parameters", {}).get("retry_after"))
            return result.get("result", {}).get("message_id")
    except urllib.error.HTTPError as exc:
        wait = retry_after_seconds((exc.headers or {}).get("Retry-After"))
        try:
            body = json.loads(exc.read(64_000))
            candidate = body.get("parameters", {}).get("retry_after")
            if isinstance(candidate, int) and not isinstance(candidate, bool) and candidate >= 0:
                wait = max(wait or 0, candidate)
        except (ValueError, AttributeError):
            pass
        raise TelegramError(retry_after=wait) from None
    except (urllib.error.URLError, TimeoutError):
        # Never include the request URL; it contains the bot token.
        raise TelegramError() from None
    except (ValueError, AttributeError):
        raise TelegramError("Réponse Telegram invalide") from None


def fingerprint(state):
    comparable = json.loads(json.dumps(state))
    for k in ("lastScanAt", "lastSuccessfulScanAt", "persistedAt", "runUrl"):
        comparable.pop(k, None)
    for p in comparable.get("products", {}).values():
        p.pop("lastCheckedAt", None)
        p.pop("lastSuccessfulAt", None)
        p.pop("lastAttemptAt", None)
    return json.dumps(comparable, sort_keys=True)


def validate_favorites(config):
    if not isinstance(config, dict) or config.get("schema") != 1:
        raise ValueError("Version de configuration inconnue")
    favorites = config.get("favorites")
    if not isinstance(favorites, list) or len(favorites) > 50:
        raise ValueError("Maximum 50 favoris par scan")
    seen = set()
    for favorite in favorites:
        if not isinstance(favorite, dict):
            raise ValueError("Favori invalide")
        url, identity = canonical_url(favorite.get("url", ""))
        if identity != favorite.get("id") or identity in seen:
            raise ValueError("Identifiant de favori invalide ou dupliqué")
        if "enabled" in favorite and not isinstance(favorite["enabled"], bool):
            raise ValueError("État de surveillance invalide")
        target = favorite.get("targetCents")
        if target is not None and (isinstance(target, bool) or not isinstance(target, int) or not 0 < target < 10_000_000):
            raise ValueError("Objectif de prix invalide")
        favorite["url"] = url
        seen.add(identity)
    return favorites


def validate_state(state):
    """Reject incompatible or corrupted history before changing any remote bytes."""
    if not isinstance(state, dict) or state.get("schema") != 1 or not isinstance(state.get("products"), dict) or not isinstance(state.get("alerts"), list):
        raise ValueError("Format d'historique incompatible ; aucune donnée remplacée")
    def valid_price(value):
        return isinstance(value, int) and not isinstance(value, bool) and 0 < value < 10_000_000
    def valid_id(value):
        return isinstance(value, str) and re.fullmatch(r"E\d{6}-\d{3}-\d{2}", value)
    for identity, product in state["products"].items():
        if not valid_id(identity) or not isinstance(product, dict) or product.get("id") != identity:
            raise ValueError("Référence d'historique invalide")
        for name in ("priceCents", "firstPriceCents", "lowestCents", "regularCents"):
            value = product.get(name)
            if value is not None and not valid_price(value):
                raise ValueError("Prix d'historique invalide")
        history = product.get("history", [])
        if not isinstance(history, list) or any(not isinstance(h, dict) or not valid_price(h.get("priceCents")) or not timestamp(h.get("at")) for h in history):
            raise ValueError("Courbe d'historique invalide")
        if product.get("url") and canonical_url(product["url"])[1] != identity:
            raise ValueError("URL d'historique incohérente")
    for event in state["alerts"]:
        if (not isinstance(event, dict) or not isinstance(event.get("id"), str) or not valid_id(event.get("productId"))
            or event.get("delivery") not in ("pending", "sent") or not valid_price(event.get("oldCents"))
            or not valid_price(event.get("newCents")) or event["newCents"] >= event["oldCents"]
            or not timestamp(event.get("at")) or canonical_url(event.get("url", ""))[1] != event["productId"]):
            raise ValueError("Alerte d'historique invalide")
    return state


def suspend_scanning(state, exc, at):
    streak = min(6, int(state.get("blockStreak", 0)) + 1)
    base = 3600 if isinstance(exc, BlockedError) and "403" in str(exc) else 900
    local_delay = min(21_600, base * 2 ** (streak - 1))
    delay = max(local_delay, getattr(exc, "retry_after", None) or 0)
    state.update({"blockStreak": streak, "cooldownUntil": after_delay(at, delay),
                  "cooldownReason": str(exc)[:140], "scanError": str(exc)[:140]})


def scan_products(state, favorites, at):
    """Bound request time and preserve successful observations on every error."""
    enabled = [f for f in favorites if f.get("enabled", True)]
    stats = {"total": len(enabled), "attempted": 0, "succeeded": 0, "failed": 0, "deferred": 0}
    state["scanStats"] = stats
    state["scanError"] = None
    if not enabled:
        state["nextScanCursor"] = 0
        return
    cooldown = timestamp(state.get("cooldownUntil"))
    if cooldown and cooldown > timestamp(at):
        stats["deferred"] = len(enabled)
        state["scanError"] = "Accès UNIQLO suspendu temporairement ; prochain essai après le délai indiqué"
        return
    state.pop("cooldownUntil", None)
    try:
        rules = Robots(get_page(ROOT + "/robots.txt"))
    except Exception as exc:
        reason = exc if isinstance(exc, BlockedError) else NetworkError("Impossible de vérifier robots.txt ; scan suspendu")
        suspend_scanning(state, reason, at)
        stats["deferred"] = len(enabled)
        return
    cursor = state.get("nextScanCursor", 0)
    cursor = cursor % len(enabled) if isinstance(cursor, int) else 0
    ordered = enabled[cursor:] + enabled[:cursor]
    deadline = time.monotonic() + SCAN_BUDGET_SECONDS
    network_failures = 0
    for position, favorite in enumerate(ordered):
        if time.monotonic() + REQUEST_TIMEOUT + REQUEST_GAP_SECONDS > deadline:
            stats["deferred"] = len(ordered) - position
            state["nextScanCursor"] = (cursor + position) % len(enabled)
            break
        stats["attempted"] += 1
        try:
            if not rules.allowed(favorite["url"]):
                raise ValueError("Collecte interdite par robots.txt")
            time.sleep(REQUEST_GAP_SECONDS)
            product = parse_product(get_page(favorite["url"]), favorite["id"])
            observe(state, favorite, product, at)
            stats["succeeded"] += 1
            network_failures = 0
            state["blockStreak"] = 0
            state.pop("cooldownReason", None)
        except Exception as exc:
            stats["failed"] += 1
            known = isinstance(exc, (ValueError, BlockedError))
            error = str(exc)[:140] if known else "Lecture UNIQLO impossible"
            item = state.setdefault("products", {}).setdefault(favorite["id"], {
                "id": favorite["id"], "url": favorite["url"],
                "name": str(favorite.get("name", "Article UNIQLO"))[:200], "history": []})
            item.update({"status": "error", "error": error, "lastAttemptAt": at})
            state["scanError"] = "Certaines fiches n'ont pas pu être vérifiées ; derniers prix valides conservés"
            network_failures = network_failures + 1 if isinstance(exc, NetworkError) else 0
            if isinstance(exc, BlockedError) or network_failures >= 3:
                suspend_scanning(state, exc, at)
                stats["deferred"] = len(ordered) - position - 1
                state["nextScanCursor"] = (cursor + position + 1) % len(enabled)
                break
    else:
        state["nextScanCursor"] = 0
    if stats["succeeded"] == stats["total"]:
        state["lastSuccessfulScanAt"] = at


def deliver_outbox(state, storage, key, at):
    if not state.get("telegramConfigured"):
        return
    retry_at = timestamp(state.get("telegramRetryAfter"))
    if retry_at and retry_at > timestamp(at):
        return
    deadline, sent = time.monotonic() + TELEGRAM_BUDGET_SECONDS, 0
    for event in state.get("alerts", []):
        if event["delivery"] != "pending":
            continue
        if sent >= MAX_TELEGRAM_PER_RUN or time.monotonic() + 10 > deadline:
            break
        event["lastAttemptAt"] = at
        event["attempts"] = event.get("attempts", 0) + 1
        try:
            message_id = telegram_send(event, os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_CHAT_ID"])
        except RuntimeError as exc:
            failures = min(6, state.get("telegramFailureCount", 0) + 1)
            delay = max(min(3600, 60 * 2 ** (failures - 1)), getattr(exc, "retry_after", None) or 0)
            state["telegramFailureCount"] = failures
            state["telegramRetryAfter"] = after_delay(at, delay)
            state["notificationError"] = "Telegram indisponible ; alertes conservées pour réessai"
            storage.save(state, key)
            break
        event.update({"delivery": "sent", "sentAt": now(), "telegramMessageId": message_id})
        sent += 1
        state.pop("notificationError", None)
        state.pop("telegramRetryAfter", None)
        state["telegramFailureCount"] = 0
        # Telegram has no idempotency key. Persist each acknowledgement before
        # another send; a process failure between send and save can still duplicate.
        storage.save(state, key)
        time.sleep(1)


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", help="Parse a local captured UNIQLO product page")
    parser.add_argument("--product-id")
    args = parser.parse_args()
    if args.fixture:
        print(json.dumps(parse_product(Path(args.fixture).read_text(), args.product_id), ensure_ascii=False, indent=2))
        return
    config_path = Path("data/watchlist.enc.json")
    key = os.getenv("UA_ENCRYPTION_KEY", "")
    if not config_path.exists() or not key:
        print("En attente de la configuration dans l'extension (clé et favoris).")
        return
    config = decrypt(json.loads(config_path.read_text()), key)
    favorites = validate_favorites(config)
    storage = GitHubState(os.environ["GITHUB_TOKEN"], os.environ["GITHUB_REPOSITORY"])
    state = validate_state(storage.load(key))
    before = fingerprint(state)
    at = now()
    state["lastScanAt"] = at
    state["runUrl"] = f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    state["telegramConfigured"] = bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))
    active = {f["id"] for f in favorites}
    state["products"] = {k: v for k, v in state.get("products", {}).items() if k in active}
    state["alerts"] = [e for e in state.get("alerts", []) if e["productId"] in active]
    scan_products(state, favorites, at)
    due = any(e["delivery"] == "pending" for e in state.get("alerts", []))
    persisted = state.get("persistedAt")
    persisted_stamp = timestamp(persisted)
    heartbeat = not persisted_stamp or (dt.datetime.now(dt.timezone.utc) - persisted_stamp).total_seconds() >= 1800
    changed = before != fingerprint(state)
    if changed or heartbeat:
        state["persistedAt"] = at
        storage.save(state, key)  # Persist outbox before attempting delivery.
    if due:
        deliver_outbox(state, storage, key, now())
    stats = state["scanStats"]
    print(f"Scan terminé : {stats['succeeded']} lecture(s) réussie(s), {stats['failed']} échec(s), {stats['deferred']} reportée(s). Données détaillées chiffrées.")
    if state.get("scanError"):
        raise RuntimeError("Collecte suspendue ; consulter l'état dans l'extension")


if __name__ == "__main__":
    try:
        run()
    except Exception:
        # Avoid leaking URLs, names, tokens and favorites in public workflow logs.
        print("Échec du scanner. Vérifier la configuration, l'accès UNIQLO et l'état chiffré.", file=sys.stderr)
        sys.exit(1)
