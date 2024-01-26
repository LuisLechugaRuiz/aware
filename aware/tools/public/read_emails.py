import base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
import os
import pickle
from typing import Optional

from aware.tools.helpers import get_private_data


def get_header(headers, name):
    for header in headers:
        if header["name"] == name:
            return header["value"]
    return None


def decode_message_part(part):
    if part["mimeType"] == "text/plain" or part["mimeType"] == "text/html":
        data = part["body"]["data"]
        return base64.urlsafe_b64decode(data).decode("utf-8")
    return None


def read_emails(num_messages: Optional[int] = 1):
    """Reads the first emails from the INBOX folder of the user's Gmail account.

    Args:
        num_messages (int, optional): The number of emails to read. Defaults to 1.

    Returns:
        str: The sender, subject, and body of each email.
    """

    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    creds = None
    credentials_file = get_private_data("credentials.json")
    token_file = get_private_data("read_email_token.pickle")

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

    service = build("gmail", "v1", credentials=creds)

    try:
        # Call the Gmail API to fetch INBOX
        results = (
            service.users().messages().list(userId="me", labelIds=["INBOX"]).execute()
        )
        messages = results.get("messages", [])

        if not messages:
            return "No messages found."
        else:
            result = ""
            for message in messages[:num_messages]:
                msg = (
                    service.users()
                    .messages()
                    .get(userId="me", id=message["id"], format="full")
                    .execute()
                )

                # Extracting message headers for sender and subject information
                headers = msg["payload"]["headers"]
                sender = get_header(headers, "From")
                subject = get_header(headers, "Subject")

                # Decoding the message body
                body = None
                if "parts" in msg["payload"]:
                    for part in msg["payload"]["parts"]:
                        body = decode_message_part(part)
                        if body:
                            break
                else:
                    body = decode_message_part(msg["payload"])

                result += f"---Message---\nSender: {sender}\nSubject: {subject}\nBody: {body}\n\n"

            return result
    except HttpError as error:
        return f"An error occurred: {error}"


def main():
    num_emails = input("number of emails to read:")
    print(read_emails(int(num_emails)))


if __name__ == "__main__":
    main()
