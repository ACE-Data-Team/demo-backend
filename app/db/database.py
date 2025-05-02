import asyncpg # type: ignore
import os
from dotenv import load_dotenv # type: ignore

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("The DATABASE_URL environment variable is not set. Please set it to proceed.")

async def get_connection():
    """
    Establishes a connection to the database using the DATABASE_URL.
    Returns:
        asyncpg.Connection: An active connection to the database.
    Raises:
        ValueError: If the connection to the database fails.
    """
    try:
        return await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        raise ValueError(f"Failed to connect to the database: {e}")
