import base64
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from requests import HTTPError
import os
import pickle

from aware.tool.helpers import get_private_data


def send_email(recipient: str, subject: str, body: str):
    """Send an email to a recipient with a subject and body.

    Args:
        recipient (str): The email address of the recipient.
        subject (str): The subject of the email.
        body (str): The body of the email.

    Returns:
        str: With the result of the email sending.
    """

    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
    creds = None
    credentials_file = get_private_data("credentials.json")
    token_file = get_private_data("send_email_token.pickle")

    # Check if token.pickle file exists with saved user credentials
    if os.path.exists(token_file):
        with open(token_file, "rb") as token:
            creds = pickle.load(token)

    # If no valid credentials available, ask the user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_file, "wb") as token:
            pickle.dump(creds, token)

    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)

    creds = flow.run_local_server(port=0)

    service = build("gmail", "v1", credentials=creds)

    message = MIMEText(body)
    message["to"] = recipient
    message["subject"] = subject
    created_message = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}

    try:
        message = (
            service.users().messages().send(userId="me", body=created_message).execute()
        )
        return "Message sent successfully!"
    except HTTPError as error:
        return f"An error occurred: {error}"
