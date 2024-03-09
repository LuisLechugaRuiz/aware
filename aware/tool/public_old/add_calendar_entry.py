import os.path
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import tzlocal
from typing import List


# Assuming get_private_data_path is a function that returns the path to a secure storage location
from aware.tool.helpers import get_private_data_path


def get_local_timezone():
    local_timezone = tzlocal.get_localzone()
    return str(local_timezone)


def add_calendar_entry(
    summary: str,
    location: str,
    description: str,
    start_time: str,
    end_time: str,
    attendees: List[str] = [],
):
    """Add an event to the user's Google Calendar.

    Args:
        summary (str): The title of the event.
        location (str): The location of the event.
        description (str): The description of the event.
        start_time (str): The start time of the event in 'YYYY-MM-DDTHH:MM:SS+HH:MM' format.
        end_time (str): The end time of the event in 'YYYY-MM-DDTHH:MM:SS+HH:MM' format.
        attendees (List[str]): A list with the email addresses to invite to the event, by default []. Will be added as {'email': attendee}
    """

    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    creds = None
    credentials_file = os.path.join(get_private_data_path(), "credentials.json")
    token_file = os.path.join(get_private_data_path(), "edit_calendar_token.pickle")

    # Check if token.pickle file exists with saved user credentials
    if os.path.exists(token_file):
        with open(token_file, "rb") as token:
            creds = pickle.load(token)

    # If no valid credentials available, log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, "wb") as token:
            pickle.dump(creds, token)

    service = build("calendar", "v3", credentials=creds)

    # Create a new calendar event
    event = {
        "summary": summary,
        "location": location,
        "description": description,
        "start": {
            "dateTime": start_time,
            "timeZone": get_local_timezone(),
        },
        "end": {
            "dateTime": end_time,
            "timeZone": get_local_timezone(),
        },
    }
    # Add attendees to the event
    if attendees:
        event["attendees"] = [{"email": attendee} for attendee in attendees]

    try:
        event = service.events().insert(calendarId="primary", body=event).execute()
        return "Event created successfully. Event ID: {}".format(event.get("id"))
    except Exception as e:
        return f"Error creating event: {e}"
