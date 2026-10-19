"""Persistent JSON store for per-guild bot config and feature data."""

from __future__ import annotations

import json
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STORE_PATH = DATA_DIR / "store.json"

_lock = threading.Lock()

_DEFAULT_GUILD: dict[str, Any] = {
    "announce_channel_id": None,
    "officers_channel_id": None,
    "onboarding": {
        "enabled": True,
        "dm_message": (
            "Welcome to Cyberspace!\n\n"
            "• Read the rules and say hi in general\n"
            "• Grab interest roles with `!roles`\n"
            "• Browse starter links with `!resources`\n"
            "• See upcoming meetings with `!events`\n"
            "• Stuck? Ask with `!helpme <topic>`\n"
        ),
        "rules_channel_id": None,
    },
    "roles": {
        "message_id": None,
        "channel_id": None,
        "options": {},
    },
    "infra": {
        "lab": {"status": "unknown", "note": ""},
        "vpn": {"status": "unknown", "note": ""},
        "vms": {"status": "unknown", "note": ""},
    },
    "moderation": {
        "secret_filter": True,
        "protected_channel_ids": [],
    },
    "calendar": {
        "enabled": True,
        "reminded": {},
    },
    "ctf": {
        "challenges": {},
        "scores": {},
    },
    "resources": {},
    "help_queue": [],
    "help_next_id": 1,
    "rsvp": {},
}


def _empty_store() -> dict[str, Any]:
    return {"guilds": {}}


def _read() -> dict[str, Any]:
    if not STORE_PATH.exists():
        return _empty_store()
    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _empty_store()


def _write(store: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(store, indent=2), encoding="utf-8")


def load_guild(guild_id: int) -> dict[str, Any]:
    with _lock:
        store = _read()
        key = str(guild_id)
        guild = store.get("guilds", {}).get(key)
        if guild is None:
            guild = deepcopy(_DEFAULT_GUILD)
            store.setdefault("guilds", {})[key] = guild
            _write(store)
            return deepcopy(guild)

        merged = deepcopy(_DEFAULT_GUILD)
        _deep_merge(merged, guild)
        return merged


def save_guild(guild_id: int, data: dict[str, Any]) -> None:
    with _lock:
        store = _read()
        store.setdefault("guilds", {})[str(guild_id)] = data
        _write(store)


def update_guild(guild_id: int, mutator) -> dict[str, Any]:
    """Load guild config, run mutator(data), save, return updated data."""
    with _lock:
        store = _read()
        key = str(guild_id)
        guild = store.get("guilds", {}).get(key)
        if guild is None:
            data = deepcopy(_DEFAULT_GUILD)
        else:
            data = deepcopy(_DEFAULT_GUILD)
            _deep_merge(data, guild)
        mutator(data)
        store.setdefault("guilds", {})[key] = data
        _write(store)
        return deepcopy(data)


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> None:
    for key, value in overlay.items():
        if (
            key in base
            and isinstance(base[key], dict)
            and isinstance(value, dict)
        ):
            _deep_merge(base[key], value)
        else:
            base[key] = value
