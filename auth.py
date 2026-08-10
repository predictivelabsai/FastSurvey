"""Local account and Google OpenID Connect helpers."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import db


def valid_email(value: str) -> str:
    value = (value or "").strip().lower()
    return value if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value) else ""


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return "scrypt$16384$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(digest).decode()


def verify_password(password: str, encoded: str | None) -> bool:
    try:
        _, cost, salt, expected = (encoded or "").split("$", 3)
        actual = hashlib.scrypt(password.encode(), salt=base64.urlsafe_b64decode(salt), n=int(cost), r=8, p=1)
        return hmac.compare_digest(actual, base64.urlsafe_b64decode(expected))
    except (ValueError, TypeError):
        return False


def register(email: str, password: str, name: str) -> tuple[dict | None, str]:
    email = valid_email(email)
    if not email:
        return None, "Enter a valid email address."
    if len(password or "") < 10:
        return None, "Use at least 10 characters for your password."
    if db.row("SELECT id FROM users WHERE email=?", (email,)):
        return None, "An account with that email already exists."
    return db.create_user(email, name, hash_password(password)), ""


def login(email: str, password: str) -> dict | None:
    user = db.row("SELECT * FROM users WHERE email=?", (valid_email(email),))
    return user if user and verify_password(password, user.get("password_hash")) else None


CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")


def google_enabled() -> bool:
    return bool(CLIENT_ID and CLIENT_SECRET)


def google_state() -> str:
    return secrets.token_urlsafe(32)


def callback_uri(request) -> str:
    if REDIRECT_URI:
        return REDIRECT_URI
    protocol = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{protocol}://{host}/auth/google/callback"


def google_authorize_url(request, state: str) -> str:
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
        "client_id": CLIENT_ID,
        "redirect_uri": callback_uri(request),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    })


def _json_request(url: str, *, data: dict | None = None, token: str | None = None) -> dict:
    body = urlencode(data).encode() if data else None
    headers = {"Accept": "application/json"}
    if data:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, data=body, headers=headers), timeout=20) as response:
        return json.loads(response.read())


def google_exchange(request, code: str) -> dict | None:
    try:
        token = _json_request("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": callback_uri(request),
            "grant_type": "authorization_code",
        })
        info = _json_request(
            "https://openidconnect.googleapis.com/v1/userinfo",
            token=token.get("access_token"),
        )
    except (HTTPError, URLError, TimeoutError, ValueError):
        return None
    email = valid_email(info.get("email", ""))
    if not email or info.get("email_verified") is False:
        return None
    domains = {item.strip().lower() for item in os.getenv("GOOGLE_ALLOWED_DOMAINS", "").split(",") if item.strip()}
    emails = {item.strip().lower() for item in os.getenv("GOOGLE_ALLOWED_EMAILS", "").split(",") if item.strip()}
    if domains or emails:
        if email not in emails and email.rsplit("@", 1)[-1] not in domains:
            return None
    return db.create_user(email, info.get("name") or email, google=True)
