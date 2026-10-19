"""Google Calendar helpers for club meeting reminders."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
ROOT = Path(__file__).resolve().parent
CREDENTIALS_PATH = ROOT / "credentials.json"
TOKEN_PATH = ROOT / "calendar_token.json"


def calendar_configured() -> bool:
    return CREDENTIALS_PATH.exists() or TOKEN_PATH.exists()


def get_calendar_service():
    if not CREDENTIALS_PATH.exists() and not TOKEN_PATH.exists():
        raise FileNotFoundError(
            "Missing credentials.json. Download OAuth client credentials "
            "from Google Cloud and place them in the project root."
        )

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    "calendar_token.json is invalid and credentials.json is missing."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def list_upcoming_events(max_results: int = 10) -> list[dict[str, Any]]:
    service = get_calendar_service()
    now = datetime.now(timezone.utc).isoformat()
    calendar_id = os.getenv("google_calendar_id", "primary")
    result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return result.get("items", [])


def parse_event_start(event: dict[str, Any]) -> datetime | None:
    start = event.get("start", {})
    raw = start.get("dateTime") or start.get("date")
    if not raw:
        return None
    if len(raw) == 10:
        return datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def events_needing_reminder(
    events: list[dict[str, Any]],
    reminded: dict[str, list[str]],
    now: datetime | None = None,
) -> list[tuple[dict[str, Any], str]]:
    """Return (event, kind) pairs for due 24h / 1h reminders."""
    now = now or datetime.now(timezone.utc)
    due: list[tuple[dict[str, Any], str]] = []

    for event in events:
        event_id = event.get("id")
        start = parse_event_start(event)
        if not event_id or start is None:
            continue

        sent = set(reminded.get(event_id, []))
        delta = start - now

        if timedelta(hours=23, minutes=30) <= delta <= timedelta(hours=24, minutes=30):
            if "24h" not in sent:
                due.append((event, "24h"))
        if timedelta(minutes=50) <= delta <= timedelta(hours=1, minutes=10):
            if "1h" not in sent:
                due.append((event, "1h"))

    return due


def format_event_line(event: dict[str, Any]) -> str:
    start = parse_event_start(event)
    title = event.get("summary") or "Untitled event"
    when = start.strftime("%a %b %d, %I:%M %p %Z") if start else "TBD"
    location = event.get("location")
    link = event.get("htmlLink")
    parts = [f"**{title}** — {when}"]
    if location:
        parts.append(f"📍 {location}")
    if link:
        parts.append(f"[Calendar]({link})")
    return "\n".join(parts)
