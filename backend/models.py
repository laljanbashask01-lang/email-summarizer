from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EmailSummary(BaseModel):
    message_id: str
    user_email: str
    sender: str
    subject: str
    snippet: str
    summary: str
    importance: str  # high, medium, low
    category: str  # work, personal, marketing, urgent
    received_at: datetime
    processed_at: datetime


class UserToken(BaseModel):
    email: str
    access_token: str
    refresh_token: str
    token_expiry: Optional[datetime] = None
