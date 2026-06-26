import os
import base64
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI")],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}


def get_auth_flow():
    """Create OAuth2 flow for Gmail authentication."""
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI"),
    )
    return flow


def get_gmail_service(access_token: str, refresh_token: str):
    """Build Gmail API service from stored credentials."""
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    )
    return build("gmail", "v1", credentials=creds)


def fetch_recent_emails(service, max_results=10):
    """Fetch recent unread emails from Gmail (inbox + spam)."""
    all_messages = []

    # Fetch from inbox
    inbox_results = service.users().messages().list(
        userId="me", labelIds=["INBOX"], maxResults=max_results
    ).execute()
    all_messages.extend(inbox_results.get("messages", []))

    # Fetch from spam folder
    spam_results = service.users().messages().list(
        userId="me", labelIds=["SPAM"], maxResults=5
    ).execute()
    all_messages.extend(spam_results.get("messages", []))

    emails = []

    for msg in all_messages:
        email_data = service.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()
        emails.append(parse_email(email_data))

    return emails


def parse_email(email_data: dict) -> dict:
    """Extract relevant fields from Gmail API response including attachments."""
    headers = email_data.get("payload", {}).get("headers", [])
    header_map = {h["name"].lower(): h["value"] for h in headers}

    body = ""
    images = []  # base64 encoded images
    attachments = []  # attachment metadata
    payload = email_data.get("payload", {})

    def extract_parts(parts):
        """Recursively extract text, images, and attachments from email parts."""
        nonlocal body
        for part in parts:
            mime_type = part.get("mimeType", "")

            # Nested multipart
            if "parts" in part:
                extract_parts(part["parts"])

            # Plain text body
            elif mime_type == "text/plain" and not body:
                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

            # HTML body (fallback if no plain text)
            elif mime_type == "text/html" and not body:
                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

            # Images
            elif mime_type.startswith("image/"):
                filename = part.get("filename", "image")
                attach_id = part.get("body", {}).get("attachmentId")
                size = part.get("body", {}).get("size", 0)
                images.append({
                    "filename": filename,
                    "mime_type": mime_type,
                    "attachment_id": attach_id,
                    "size": size,
                })

            # Other attachments (PDF, docs, etc.)
            elif part.get("filename"):
                attach_id = part.get("body", {}).get("attachmentId")
                size = part.get("body", {}).get("size", 0)
                attachments.append({
                    "filename": part["filename"],
                    "mime_type": mime_type,
                    "attachment_id": attach_id,
                    "size": size,
                })

    if "parts" in payload:
        extract_parts(payload["parts"])
    elif "body" in payload and payload["body"].get("data"):
        body = base64.urlsafe_b64decode(
            payload["body"]["data"]
        ).decode("utf-8", errors="ignore")

    return {
        "message_id": email_data["id"],
        "sender": header_map.get("from", "Unknown"),
        "subject": header_map.get("subject", "No Subject"),
        "snippet": email_data.get("snippet", ""),
        "body": body[:3000],
        "images": images,
        "attachments": attachments,
        "has_attachments": len(images) + len(attachments) > 0,
        "received_at": datetime.fromtimestamp(
            int(email_data.get("internalDate", "0")) / 1000
        ),
    }
