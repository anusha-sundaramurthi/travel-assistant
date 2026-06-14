"""
Client store — manages client accounts in data/clients.json.
Each client has their own login, api_key, and owns their bots.
Super admin is hardcoded via .env variables.
"""

import json
import os
import uuid
from datetime import datetime

from src.auth import hash_password, verify_password

CLIENTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "clients.json"
)


def _load() -> dict:
    os.makedirs(os.path.dirname(CLIENTS_FILE), exist_ok=True)
    if not os.path.exists(CLIENTS_FILE):
        return {}
    with open(CLIENTS_FILE, "r") as f:
        return json.load(f)


def _save(data: dict):
    os.makedirs(os.path.dirname(CLIENTS_FILE), exist_ok=True)
    with open(CLIENTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ── Super admin (from .env) ───────────────────────────────
SUPER_ADMIN_EMAIL    = os.getenv("SUPER_ADMIN_EMAIL",    "admin@yourdomain.com")
SUPER_ADMIN_PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD", "changeme123")
SUPER_ADMIN_ID       = "super_admin"


def _super_admin_record() -> dict:
    return {
        "client_id":      SUPER_ADMIN_ID,
        "email":          SUPER_ADMIN_EMAIL,
        "name":           "Super Admin",
        "api_key":        "super_admin_key",
        "is_super_admin": True,
        "created_at":     "system",
    }


# ── Create client ─────────────────────────────────────────
def create_client(name: str, email: str, password: str) -> dict:
    clients = _load()

    # Check email unique
    for c in clients.values():
        if c["email"].lower() == email.lower():
            raise ValueError(f"Email {email} already registered")

    client_id = "client_" + uuid.uuid4().hex[:10]
    api_key   = "ak_" + uuid.uuid4().hex[:16]

    client = {
        "client_id":      client_id,
        "email":          email.lower().strip(),
        "name":           name,
        "password_hash":  hash_password(password),
        "api_key":        api_key,
        "is_super_admin": False,
        "created_at":     datetime.utcnow().isoformat(),
    }
    clients[client_id] = client
    _save(clients)

    # Return without password hash
    return _safe(client)


# ── Authenticate ──────────────────────────────────────────
def authenticate(email: str, password: str) -> dict | None:
    """
    Returns client record (without password_hash) if credentials valid,
    else None.
    Handles super admin separately — no bcrypt needed.
    """
    # Super admin check
    if email.lower().strip() == SUPER_ADMIN_EMAIL.lower().strip():
        if password == SUPER_ADMIN_PASSWORD:
            return _super_admin_record()
        return None

    clients = _load()
    for c in clients.values():
        if c["email"] == email.lower().strip():
            if verify_password(password, c["password_hash"]):
                return _safe(c)
            return None
    return None


# ── Lookup ────────────────────────────────────────────────
def get_client(client_id: str) -> dict | None:
    if client_id == SUPER_ADMIN_ID:
        return _super_admin_record()
    return _safe(_load().get(client_id))


def get_client_by_api_key(api_key: str) -> dict | None:
    """Used by widget to verify api_key."""
    for c in _load().values():
        if c.get("api_key") == api_key:
            return _safe(c)
    return None


def get_all_clients() -> list[dict]:
    """Super admin only — list all clients."""
    return [_safe(c) for c in _load().values()]


def delete_client(client_id: str):
    clients = _load()
    if client_id in clients:
        del clients[client_id]
        _save(clients)


def _safe(client: dict | None) -> dict | None:
    """Strip password_hash before returning."""
    if client is None:
        return None
    return {k: v for k, v in client.items() if k != "password_hash"}