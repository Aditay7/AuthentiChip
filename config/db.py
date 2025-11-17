import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB", "testdb")

if not MONGO_URI:
    raise RuntimeError("MONGODB_URI not set in environment (.env)")


client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]


def close_client():
    client.close()
