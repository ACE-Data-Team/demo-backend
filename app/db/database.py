import asyncpg # type: ignore
import os
from dotenv import load_dotenv # type: ignore

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise ValueError("The DATABASE_URL environment variable is not set. Please set it to proceed.")

async def get_connection():
    return await asyncpg.connect(DATABASE_URL)
