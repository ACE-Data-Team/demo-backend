
# database.py
import asyncpg # type: ignore
import os
import pandas as pd # type: ignore
from dotenv import load_dotenv # type: ignore
import logging
from typing import Optional
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("The DATABASE_URL environment variable is not set. Please set it to proceed.")

# Global connection pool
_pool: Optional[asyncpg.Pool] = None

async def init_db_pool():
    """Initialize the database connection pool"""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
    return _pool

async def get_pool():
    """Get the connection pool, initialize if needed"""
    if _pool is None:
        await init_db_pool()
    return _pool

async def close_pool():
    """Close the connection pool"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None

# Performance timing decorator
def time_db_operation(operation_name: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"DB Operation '{operation_name}' completed in {duration:.4f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"DB Operation '{operation_name}' failed after {duration:.4f}s: {e}")
                raise
        return wrapper
    return decorator

def build_query_with_faculty(base_query: str, faculty: str = None):
    """
    Builds a SQL query with an optional WHERE clause for faculty.
    """

    if faculty:
        return f"{base_query} WHERE faculty = $1", [faculty]
    return base_query, []


@time_db_operation("fetch_student_data")
async def fetch_student_data(conn, faculty: str = None):
    """Fetch student data using connection pool"""
    pool = await get_pool()
    base_query = "SELECT session, type, count FROM student"
    query, params = build_query_with_faculty(base_query, faculty)

    async with pool.acquire() as conn:
        return await conn.fetch(query, *params)

@time_db_operation("fetch_staff_data")
async def fetch_staff_data(conn, faculty: str = None):
    """Fetch academic staff data using connection pool"""
    pool = await get_pool()
    base_query = "SELECT session, position, count FROM academic_staff"
    query, params = build_query_with_faculty(base_query, faculty)

    async with pool.acquire() as conn:
        return await conn.fetch(query, *params)


@time_db_operation("get_student_dataframe")
async def get_student_dataframe(faculty: str = None):
    """
    Fetches student data and returns it as a pandas DataFrame.
    """
    data = await fetch_student_data(faculty)
    # Convert to list of dictionaries for pandas
    data_dicts = [dict(row) for row in data]
    df = pd.DataFrame(data_dicts)
    logger.info(f"Retrieved {len(df)} student records")
    return df


@time_db_operation("get_staff_dataframe")
async def get_staff_dataframe(faculty: str = None):
    """
    Fetches academic staff data and returns it as a pandas DataFrame.
    Args:
        faculty (str, optional): Faculty filter. Defaults to None.
    Returns:
        pd.DataFrame: DataFrame containing academic staff data.
    """
    data = await fetch_staff_data(faculty)
    # Convert to list of dictionaries for pandas
    data_dicts = [dict(row) for row in data]
    df = pd.DataFrame(data_dicts)
    logger.info(f"Retrieved {len(df)} staff records")
    return df


