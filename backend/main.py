import os
import asyncio
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from dotenv import load_dotenv

try:
    from backend.database import init_db, emails_collection, users_collection
    from backend.gmail_service import get_auth_flow, get_gmail_service, fetch_recent_emails
    from backend.llm_service import summarize_email
except ImportError:
    from database import init_db, emails_collection, users_collection
    from gmail_service import get_auth_flow, get_gmail_service, fetch_recent_emails
    from llm_service import summarize_email

load_dotenv()

# WebSocket connection manager
connected_clients: list[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Start background email polling
    task = asyncio.create_task(poll_emails())
    yield
    task.cancel()


app = FastAPI(title="Email Summarizer", lifespan=lifespan)

# Resolve frontend path relative to this file
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# Serve frontend
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def root():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


# --- Auth Endpoints ---

# Store code verifier between auth steps
_auth_state = {}


@app.get("/auth/login")
async def login():
    """Redirect user to Google OAuth2 consent screen."""
    flow = get_auth_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline", prompt="consent"
    )
    # Save the code verifier for the callback
    _auth_state[state] = flow.code_verifier
    return RedirectResponse(auth_url)


@app.get("/auth/callback")
async def auth_callback(code: str, state: str = None):
    """Handle OAuth2 callback and store tokens."""
    flow = get_auth_flow()
    # Restore the code verifier
    if state and state in _auth_state:
        flow.code_verifier = _auth_state.pop(state)
    flow.fetch_token(code=code)
    credentials = flow.credentials

    # Get user email
    service = get_gmail_service(credentials.token, credentials.refresh_token)
    profile = service.users().getProfile(userId="me").execute()
    user_email = profile["emailAddress"]

    # Store credentials
    await users_collection.update_one(
        {"email": user_email},
        {"$set": {
            "email": user_email,
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "authenticated_at": datetime.utcnow(),
        }},
        upsert=True,
    )

    return RedirectResponse("/?authenticated=true")


# --- Email Endpoints ---

@app.get("/api/emails")
async def get_emails(limit: int = 20):
    """Get processed email summaries from database."""
    cursor = emails_collection.find().sort("received_at", -1).limit(limit)
    emails = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        emails.append(doc)
    return emails


@app.post("/api/fetch-emails")
async def trigger_fetch():
    """Manually trigger email fetch and processing."""
    user = await users_collection.find_one()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    service = get_gmail_service(user["access_token"], user["refresh_token"])
    raw_emails = fetch_recent_emails(service, max_results=5)

    processed = []
    for email in raw_emails:
        # Check if already processed
        existing = await emails_collection.find_one(
            {"message_id": email["message_id"]}
        )
        if existing:
            continue

        # Summarize with LLM
        llm_result = await summarize_email(
            email["sender"], email["subject"], email["body"]
        )

        email_doc = {
            "message_id": email["message_id"],
            "user_email": user["email"],
            "sender": email["sender"],
            "subject": email["subject"],
            "snippet": email["snippet"],
            "summary": llm_result["summary"],
            "importance": llm_result["importance"],
            "category": llm_result["category"],
            "sentiment": llm_result["sentiment"],
            "tone": llm_result["tone"],
            "spam_classification": llm_result["spam_classification"],
            "spam_confidence": llm_result["spam_confidence"],
            "threat_level": llm_result["threat_level"],
            "action_required": llm_result["action_required"],
            "reply_urgency": llm_result["reply_urgency"],
            "suggested_reply": llm_result["suggested_reply"],
            "key_points": llm_result["key_points"],
            "emotional_cues": llm_result["emotional_cues"],
            "red_flags": llm_result["red_flags"],
            "received_at": email["received_at"],
            "processed_at": datetime.utcnow(),
        }

        await emails_collection.insert_one(email_doc)
        email_doc["_id"] = str(email_doc["_id"])
        processed.append(email_doc)

        # Notify connected WebSocket clients
        await broadcast_notification(email_doc)

    return {"processed": len(processed), "emails": processed}


# --- WebSocket for Real-time Notifications ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


async def broadcast_notification(email_doc: dict):
    """Send new email notification to all connected clients."""
    import json

    message = json.dumps({
        "type": "new_email",
        "data": {
            "subject": email_doc["subject"],
            "sender": email_doc["sender"],
            "summary": email_doc["summary"],
            "importance": email_doc["importance"],
            "category": email_doc["category"],
        }
    }, default=str)

    for client in connected_clients[:]:
        try:
            await client.send_text(message)
        except Exception:
            connected_clients.remove(client)


async def poll_emails():
    """Background task to poll for new emails every 60 seconds."""
    while True:
        await asyncio.sleep(60)
        try:
            user = await users_collection.find_one()
            if user:
                service = get_gmail_service(
                    user["access_token"], user["refresh_token"]
                )
                raw_emails = fetch_recent_emails(service, max_results=3)

                for email in raw_emails:
                    existing = await emails_collection.find_one(
                        {"message_id": email["message_id"]}
                    )
                    if existing:
                        continue

                    llm_result = await summarize_email(
                        email["sender"], email["subject"], email["body"]
                    )

                    email_doc = {
                        "message_id": email["message_id"],
                        "user_email": user["email"],
                        "sender": email["sender"],
                        "subject": email["subject"],
                        "snippet": email["snippet"],
                        "summary": llm_result["summary"],
                        "importance": llm_result["importance"],
                        "category": llm_result["category"],
                        "sentiment": llm_result["sentiment"],
                        "tone": llm_result["tone"],
                        "spam_classification": llm_result["spam_classification"],
                        "spam_confidence": llm_result["spam_confidence"],
                        "threat_level": llm_result["threat_level"],
                        "action_required": llm_result["action_required"],
                        "reply_urgency": llm_result["reply_urgency"],
                        "suggested_reply": llm_result["suggested_reply"],
                        "key_points": llm_result["key_points"],
                        "emotional_cues": llm_result["emotional_cues"],
                        "red_flags": llm_result["red_flags"],
                        "received_at": email["received_at"],
                        "processed_at": datetime.utcnow(),
                    }

                    await emails_collection.insert_one(email_doc)
                    email_doc["_id"] = str(email_doc["_id"])
                    await broadcast_notification(email_doc)
        except Exception as e:
            print(f"Polling error: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
