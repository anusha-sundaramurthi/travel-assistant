"""
Bot store — manages bot configs per client.
Each bot belongs to a client_id.
Super admin can see all bots.
"""

import json
import os
import uuid
from datetime import datetime

BOTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "bots.json"
)


def _load() -> dict:
    os.makedirs(os.path.dirname(BOTS_FILE), exist_ok=True)
    if not os.path.exists(BOTS_FILE):
        return {}
    with open(BOTS_FILE, "r") as f:
        return json.load(f)


def _save(data: dict):
    os.makedirs(os.path.dirname(BOTS_FILE), exist_ok=True)
    with open(BOTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def create_bot(
    client_id:       str,
    client_api_key:  str,
    name:            str,
    welcome_message: str,
    primary_color:   str
) -> dict:
    bots   = _load()
    bot_id = "bot_" + uuid.uuid4().hex[:10]
    bot    = {
        "bot_id":          bot_id,
        "client_id":       client_id,
        "api_key":         client_api_key,   # same as client's api_key
        "name":            name,
        "welcome_message": welcome_message,
        "primary_color":   primary_color,
        "collection_name": bot_id,
        "pdfs":            [],
        "created_at":      datetime.utcnow().isoformat(),
    }
    bots[bot_id] = bot
    _save(bots)
    return bot


def get_bot(bot_id: str) -> dict | None:
    return _load().get(bot_id)


def get_bots_for_client(client_id: str) -> list[dict]:
    """Return only bots owned by this client."""
    return [b for b in _load().values() if b["client_id"] == client_id]


def get_all_bots() -> list[dict]:
    """Super admin only."""
    return list(_load().values())


def get_bot_by_api_key_and_id(bot_id: str, api_key: str) -> dict | None:
    """Verify bot exists AND api_key matches its owner."""
    bot = _load().get(bot_id)
    if bot and bot.get("api_key") == api_key:
        return bot
    return None


def add_pdf(bot_id: str, filename: str):
    bots = _load()
    if bot_id not in bots:
        raise ValueError(f"Bot {bot_id} not found")
    if filename not in bots[bot_id]["pdfs"]:
        bots[bot_id]["pdfs"].append(filename)
    _save(bots)


def update_bot(
    bot_id: str, client_id: str,
    name: str, welcome_message: str, primary_color: str
) -> dict:
    bots = _load()
    if bot_id not in bots:
        raise ValueError("Bot not found")
    if bots[bot_id]["client_id"] != client_id:
        raise PermissionError("Not your bot")
    bots[bot_id]["name"]            = name
    bots[bot_id]["welcome_message"] = welcome_message
    bots[bot_id]["primary_color"]   = primary_color
    _save(bots)
    return bots[bot_id]


def delete_bot(bot_id: str, client_id: str, is_super_admin: bool = False):
    bots = _load()
    if bot_id not in bots:
        raise ValueError("Bot not found")
    if not is_super_admin and bots[bot_id]["client_id"] != client_id:
        raise PermissionError("Not your bot")
    del bots[bot_id]
    _save(bots)