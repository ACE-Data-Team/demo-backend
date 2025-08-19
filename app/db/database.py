import asyncpg  # type: ignore
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import pandas as pd  # type: ignore
from dotenv import load_dotenv  # type: ignore
import logging
from typing import Optional, Tuple, List, Any, Dict 
import time
from contextlib import asynccontextmanager
from functools import wraps

# logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("The DATABASE_URL environment variable is not set. Please set it to proceed.")

# SQLAlchemy ORM setup 
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Async Database Manager
class DatabaseManager:
    """Database connection pool lifecycle manager."""

    def __init__(self) -> None:
        self._pool: Optional[asyncpg.Pool] = None

    async def init_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=60,
            )
            logger.info("Initialized asyncpg pool")
        return self._pool

    async def get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            await self.init_pool()
        assert self._pool is not None
        return self._pool

    async def close_pool(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("Closed asyncpg pool")

    @asynccontextmanager
    async def get_connection(self):
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            yield conn


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions for backward compatibility
async def init_db_pool() -> asyncpg.Pool:
    return await db_manager.init_pool()

async def get_pool() -> asyncpg.Pool:
    return await db_manager.get_pool()

async def close_pool() -> None:
    await db_manager.close_pool()


# Performance timing decorator
def time_db_operation(operation_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"DB Operation '{operation_name}' completed in {duration:.4f}s")
                return result
            except Exception:
                duration = time.time() - start_time
                logger.exception(f"DB Operation '{operation_name}' failed after {duration:.4f}s")
                raise

        return wrapper
    return decorator



def append_filter(query: str, params: List[Any], column: str, value: Any) -> Tuple[str, List[Any]]:
    """Append a filter `column = $n` to the query and update params."""
    if value is None:
        return query, params

    param_index = len(params) + 1
    clause = f"{column} = ${param_index}"
    if "WHERE" in query.upper():
        query = f"{query} AND {clause}"
    else:
        query = f"{query} WHERE {clause}"

    params = params + [value]
    return query, params


# Specific convenience filter wrappers for column names
def append_faculty(query: str, params: List[Any], faculty: Optional[str]) -> Tuple[str, List[Any]]:
    return append_filter(query, params, "faculty", faculty)


def append_session(query: str, params: List[Any], session: Optional[str]) -> Tuple[str, List[Any]]:
    return append_filter(query, params, "session", session)


def append_gender(query: str, params: List[Any], gender: Optional[str]) -> Tuple[str, List[Any]]:
    return append_filter(query, params, "gender", gender)


def append_type(query: str, params: List[Any], student_type: Optional[str]) -> Tuple[str, List[Any]]:
    return append_filter(query, params, "type", student_type)


def append_level(query: str, params: List[Any], level: Optional[str]) -> Tuple[str, List[Any]]:
    return append_filter(query, params, "level", level)



# Generic Fetch Function
@time_db_operation("fetch_data")
async def fetch_data(
    table: str,
    columns: List[str],
    filters: Optional[Dict[str, Any]] = None,
    base_where: Optional[str] = None,
) -> List[asyncpg.Record]:
    """
    Generic function to fetch data from a table with optional filters.
    - `filters`: dict of {column: value}
    - `base_where`: raw WHERE clause string (e.g. "type = 'Undergraduate'")
    """
    query = f"SELECT {', '.join(columns)} FROM {table}"
    params: List[Any] = []

    if base_where:
        query += f" WHERE {base_where}"

    if filters:
        for col, val in filters.items():
            query, params = append_filter(query, params, col, val)

    async with db_manager.get_connection() as conn:
        return await conn.fetch(query, *params)


@time_db_operation("fetch_student_data")
async def fetch_student_data(faculty: Optional[str] = None, session: Optional[str] = None) -> List[asyncpg.Record]:
    """Fetch student data using optional faculty and session filter."""
    base_query = "SELECT session, type, count FROM student"
    query, params = [], []
    query = base_query
    query, params = append_faculty(query, params, faculty)
    query, params = append_session(query, params, session)

    async with db_manager.get_connection() as conn:
        return await conn.fetch(query, *params)


@time_db_operation("fetch_staff_data")
async def fetch_staff_data(faculty: Optional[str] = None, session: Optional[str] = None) -> List[asyncpg.Record]:
    """Fetch academic staff data with optional faculty and session filter."""
    base_query = "SELECT session, position, count FROM academic_staff"
    query, params = base_query, []
    query, params = append_faculty(query, params, faculty)
    query, params = append_session(query, params, session)

    async with db_manager.get_connection() as conn:
        return await conn.fetch(query, *params)

@time_db_operation("fetch_enrollment_data")
async def fetch_enrollment_data(session: Optional[str] = None):
    base_query = "SELECT session, count FROM enrollment_data"
    query, params = base_query, []
    query, params = append_session(query, params, session)

    async with db_manager.get_connection() as conn:
        return await conn.fetch(query, *params)

@time_db_operation("fetch_count_by_filter_undergraduate")
async def fetch_count_by_filter_undergraduate(
    faculty: Optional[str] = None, student_type: Optional[str] = None, level: Optional[str] = None, session: Optional[str] = None
) -> List[asyncpg.Record]:
    """Fetch undergraduate student counts with composable filters."""
    base_query = "SELECT session, type, level, count FROM enrollment_data WHERE type = 'Undergraduate'"
    query = base_query
    params: List[Any] = []

    # Note: base_query already contains WHERE type = 'Undergraduate'
    query, params = append_level(query, params, level)
    query, params = append_type(query, params, student_type)
    query, params = append_faculty(query, params, faculty)
    query, params = append_session(query, params, session)

    async with db_manager.get_connection() as conn:
        return await conn.fetch(query, *params)


@time_db_operation("fetch_count_by_filter_postgraduate")
async def fetch_count_by_filter_postgraduate(
    faculty: Optional[str] = None, student_type: Optional[str] = None, level: Optional[str] = None, session: Optional[str] = None
) -> List[asyncpg.Record]:
    """Fetch postgraduate student counts with composable filters."""
    base_query = "SELECT session, type, level, count FROM enrollment_data WHERE type = 'Postgraduate'"
    query = base_query
    params: List[Any] = []

    query, params = append_level(query, params, level)
    query, params = append_type(query, params, student_type)
    query, params = append_faculty(query, params, faculty)
    query, params = append_session(query, params, session)

    async with db_manager.get_connection() as conn:
        return await conn.fetch(query, *params)


@time_db_operation("get_student_dataframe")
async def get_student_dataframe(faculty: Optional[str] = None, session: Optional[str] = None) -> pd.DataFrame:
    """Return student data as a pandas DataFrame."""
    data = await fetch_student_data(faculty, session)
    data_dicts = [dict(row) for row in data] if data else []
    df = pd.DataFrame(data_dicts)
    logger.info(f"Retrieved {len(df)} student records")
    return df


@time_db_operation("get_staff_dataframe")
async def get_staff_dataframe(faculty: Optional[str] = None, session: Optional[str] = None) -> pd.DataFrame:
    """Return staff data as a pandas DataFrame."""
    data = await fetch_staff_data(faculty, session)
    data_dicts = [dict(row) for row in data] if data else []
    df = pd.DataFrame(data_dicts)
    logger.info(f"Retrieved {len(df)} staff records")
    return df


@time_db_operation("get_enrollment_dataframe")
async def get_enrollment_dataframe(session: Optional[str] = None)-> pd.DataFrame:
    data = await fetch_enrollment_data(session)
    data_dicts = [dict(row) for row in data] if data else []
    df = pd.DataFrame(data_dicts)
    logger.info(f"Retrieved {len(df)} staff records")
    return df


@time_db_operation("get_enrollment_dataframe2")
async def get_enrollment_dataframe2(
    faculty: Optional[str] = None, student_type: Optional[str] = None, level: Optional[str] = None, session: Optional[str] = None
) -> pd.DataFrame:
    """Return enrollment data (undergrad/postgrad) as a pandas DataFrame.

    If student_type is provided it should be exactly 'Undergraduate' or 'Postgraduate'.
    """
    if student_type == "Undergraduate":
        data = await fetch_count_by_filter_undergraduate(faculty, student_type, level, session)
    elif student_type == "Postgraduate":
        data = await fetch_count_by_filter_postgraduate(faculty, student_type, level, session)
    else:
        raise ValueError("Invalid student type. Must be 'Undergraduate' or 'Postgraduate'.")

    data_dicts = [dict(row) for row in data] if data else []
    df = pd.DataFrame(data_dicts)
    logger.info(f"Retrieved {len(df)} enrollment records")
    return df


# Context manager for application lifecycle
@asynccontextmanager
async def database_lifecycle():
    """Context manager for proper database initialization and cleanup."""
    try:
        await db_manager.init_pool()
        logger.info("Database connection pool initialized")
        yield db_manager
    finally:
        await db_manager.close_pool()
        logger.info("Database connection pool closed")


#  # small utility to convert asyncpg.Record list to pandas DataFrame
# def records_to_dataframe(records: List[asyncpg.Record]) -> pd.DataFrame:
#     if not records:
#         return pd.DataFrame()
#     return pd.DataFrame([dict(r) for r in records])

