from calendar import calendar
import os
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CALENDAR_ID = "04a68f83eba04825174a7d7e2eee1b80f9df253f999b9649034b3264a3c42a56@group.calendar.google.com"

CALENDAR_NAME = "Cyberspace Calendar"

# Read-only access to Google Calendar
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly"
]

# File with saved Google auth
TOKEN_FILE = "calendar_token.json"

# gets google calendar authentication 
def get_credentials():
    creds = None

    # Check for authorization
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE, SCOPES
        )

    # Refresh expired creds if possible
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

        with open(TOKEN_FILE, "w") as file:
            file.write(creds.to_json())

    # Ask the user to authorize 
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json.", SCOPES
        )

        creds = flow.run_local_server(port=0)

        # Save authorization for future use
        with open(TOKEN_FILE, "w") as file:
            file.write(creds.to_json())

    return creds

creds = get_credentials()


def get_next_event():
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)

    # Retrieve the specific shared calendar
    print("Requested Calendar ID:", repr(CALENDAR_ID))

    calendar = service.calendarList().get(
        calendarId=CALENDAR_ID
    ).execute()

    print("Returned Calendar ID:", calendar.get("id"))
    print("Calendar Name:", calendar.get("summary"))
    print("Display Name:", calendar.get("summaryOverride"))

    # Check the calendar's name
    name = calendar.get("summaryOverride") or calendar.get("summary")

    if name != CALENDAR_NAME:
        raise ValueError(
            f"Wrong calendar! Expected {CALENDAR_NAME}, found {name}"
        )

    print(f"Connected to: {name}")

    # Retrieve upcoming events
    now = datetime.now(timezone.utc).isoformat()

    results = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = results.get("items", [])

    return events[0] if events else None




if __name__ == "__main__":
    try:
        event = get_next_event()

        if event:
            print("Next event:", event.get("summary", "Untitled"))
            print("Starts:", event["start"])
        else:
            print("No upcoming events found!")

    except Exception as error:
        print(f"Error: {error}")