import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "email_summarizer")

client = AsyncIOMotorClient(MONGODB_URI)
db = client[DATABASE_NAME]

emails_collection = db["emails"]
users_collection = db["users"]


async def init_db():
    """Create indexes for efficient queries."""
    await emails_collection.create_index("message_id", unique=True)
    await emails_collection.create_index("user_email")
    await emails_collection.create_index("importance")
    await emails_collection.create_index("received_at")
