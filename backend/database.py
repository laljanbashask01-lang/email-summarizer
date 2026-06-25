import os
import ssl
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "email_summarizer")

# Create custom SSL context with certifi certificates
ssl_context = ssl.create_default_context(cafile=certifi.where())

client = AsyncIOMotorClient(
    MONGODB_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000,
)
db = client[DATABASE_NAME]

emails_collection = db["emails"]
users_collection = db["users"]


async def init_db():
    """Create indexes for efficient queries."""
    try:
        await emails_collection.create_index("message_id", unique=True)
        await emails_collection.create_index("user_email")
        await emails_collection.create_index("importance")
        await emails_collection.create_index("received_at")
        print("Database connected and indexes created.")
    except Exception as e:
        print(f"Database init warning: {e}")
