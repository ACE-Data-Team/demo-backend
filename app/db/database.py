import asyncpg # type: ignore
import os
from dotenv import load_dotenv # type: ignore

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def get_connection():
    return await asyncpg.connect(DATABASE_URL)
