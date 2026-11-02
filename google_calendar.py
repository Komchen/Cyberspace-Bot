import os
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# Read-only access to Google Calendar
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly"
]

# Calendar to retrieve events
CALENDAR_ID = "primary"

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
            "credentials.json.json", SCOPES
        )

        creds = flow.run_local_server(port=0)

        # Save authorization for future use
        with open(TOKEN_FILE, "w") as file:
            file.write(creds.to_json())

    return creds

creds = get_credentials()


def get_next_event():
# Gtes permission to access the calendar, then requests the next event,
#  returns result ordred by starting time


    # Get authorized Google credentials
    creds = get_credentials()

    # Connect to Google Calendar API
    service = build("calendar", "v3", credentials=creds)

    # Get current time in UTC
    now = datetime.now(timezone.utc).isoformat()

    # Ask Google for upcoming events
    results = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = results.get("items", [])

    # No events found
    if not events:
        return None

    # Return the first upcoming event
    return events[0]




#run w/o discord to test
if __name__ == "__main__":
    event = get_next_event()

    if event:
        print("Next event:", event.get("summary", "Untitled"))
        print("Starts:", event["start"])
    else:
        print("No upcoming events!")