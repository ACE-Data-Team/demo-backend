import asyncpg # type: ignore
import os
import pandas as pd # type: ignore
from dotenv import load_dotenv # type: ignore
import logging
from typing import Optional
import time
from contextlib import asynccontextmanager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("The DATABASE_URL environment variable is not set. Please set it to proceed.")

class DatabaseManager:
    """Database connection manager lifecycle management"""
    
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
    
    async def init_pool(self):
        """Initialize the database connection pool"""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
        return self._pool
    
    async def get_pool(self):
        """Get the connection pool, initialize if needed"""
        if self._pool is None:
            await self.init_pool()
        return self._pool
    
    async def close_pool(self):
        """Close the connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    @asynccontextmanager
    async def get_connection(self):
        """Context manager for getting database connections"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            yield conn

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions for backward compatibility
async def init_db_pool():
    """Initialize the database connection pool"""
    return await db_manager.init_pool()

async def get_pool():
    """Get the connection pool, initialize if needed"""
    return await db_manager.get_pool()

async def close_pool():
    """Close the connection pool"""
    await db_manager.close_pool()

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
    """Build query with faculty filter"""
    if faculty:
        return f"{base_query} WHERE faculty = $1", [faculty]
    return base_query, []

def build_query_with_session(base_query: str, session: str = None):
    """Build query with session filter"""
    if session:
        return f"{base_query} WHERE session = $1", [session]
    return base_query, []

def build_query_with_faculty_and_session(base_query: str, faculty: str = None, session: str = None):
    """Build query with optional faculty and session filters"""
    query, params = build_query_with_faculty(base_query, faculty)
    if session:
        query, session_params = build_query_with_session(query, session)
        params.extend(session_params)
    return query, params

def build_query_with_gender(base_query: str, student_gender: str = None):
    """Build query with student gender filter"""
    if student_gender:
        return f"{base_query} WHERE gender = $1", [student_gender]
    return base_query, []

def build_query_with_type(base_query: str, student_type: str = None):
    """Build query with optional student type filter"""
    if student_type:
        return f"{base_query} WHERE type = $1", [student_type]
    return base_query, []

def build_query_with_level(base_query: str, level: str = None):
    """Build query with optional student level filter"""
    if level:
        query = f"{base_query} WHERE level = $1"
        return query, [level]
    return base_query, []

def build_query_with_type_and_level(base_query: str, student_type: str = None, level: str = None):
    """Build query with optional student type and level filters"""
    if student_type and level:
        return f"{base_query} WHERE type = $1 AND level = $2", [student_type, level]
    elif student_type:
        return f"{base_query} WHERE type = $1", [student_type]
    elif level:
        return f"{base_query} WHERE level = $1", [level]
    return base_query, []



@time_db_operation("fetch_student_data")
async def fetch_student_data(faculty: str = None):
    """Fetch student data using connection pool"""
    base_query = "SELECT session, type, count FROM student"
    query, params = build_query_with_faculty(base_query, faculty)

    async with db_manager.get_connection() as conn:
        return await conn.fetch(query, *params)

@time_db_operation("fetch_staff_data")
async def fetch_staff_data(faculty: str = None):
    """Fetch academic staff data using connection pool"""
    base_query = "SELECT session, position, count FROM academic_staff"
    query, params = build_query_with_faculty(base_query, faculty)

    async with db_manager.get_connection() as conn:
        return await conn.fetch(query, *params)

@time_db_operation("fetch_count_by_filter_undergraduate")
async def fetch_count_by_filter_undergraduate(faculty: str = None, student_type: str = None, level: str = None):
    """
    Fetch undergraduate student count data with type filters.
    
    Args:
        faculty (str, optional): Faculty filter. Defaults to None.
        student_type (str, optional): Student type filter. Defaults to None.
        level (str, optional): Student level filter. Defaults to None.
    
    Returns:
        list: List of student records matching the filters.
    """
    base_query = "SELECT session, type, level, count FROM enrollment_data WHERE type = 'Undergraduate'"
    query, params = build_query_with_type_and_level(base_query, student_type, level)
    query, params = build_query_with_faculty(query, faculty)

    async with db_manager.get_connection() as conn:
        return await conn.fetch(query, *params)
    
@time_db_operation("fetch_count_by_filter_postgraduate")
async def fetch_count_by_filter_postgraduate(faculty: str = None, student_type: str = None, level: str = None):
    """
    Fetch postgraduate student count data with type filters.
    
    Args:
        faculty (str, optional): Faculty filter. Defaults to None.
        student_type (str, optional): Student type filter. Defaults to None.
        level (str, optional): Student level filter. Defaults to None.
    
    Returns:
        list: List of student records matching the filters.
    """
    base_query = "SELECT session, type, level, count FROM enrollment_data WHERE type = 'Postgraduate'"
    query, params = build_query_with_type_and_level(base_query, student_type, level)
    query, params = build_query_with_faculty(query, faculty)

    async with db_manager.get_connection() as conn:
        return await conn.fetch(query, *params)



@time_db_operation("get_student_dataframe")
async def get_student_dataframe(faculty: str = None):
    """
    Fetches student data and returns it as a pandas DataFrame.
    
    Args:
        faculty (str, optional): Faculty filter. Defaults to None.
    
    Returns:
        pd.DataFrame: DataFrame containing student data.
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
    return 

@time_db_operation("get_enrollment_dataframe")
async def get_enrollment_dataframe(faculty: str = None, student_type: str = None, level: str = None):
    """
    Fetches enrollment data and returns it as a pandas DataFrame.
    
    Args:
        faculty (str, optional): Faculty filter. Defaults to None.
        student_type (str, optional): Student type filter. Defaults to None.
        level (str, optional): Student level filter. Defaults to None.
    
    Returns:
        pd.DataFrame: DataFrame containing enrollment data.
    """
    if student_type == "Undergraduate":
        data = await fetch_count_by_filter_undergraduate(faculty, student_type, level)
    elif student_type == "Postgraduate":
        data = await fetch_count_by_filter_postgraduate(faculty, student_type, level)
    else:
        raise ValueError("Invalid student type. Must be 'Undergraduate' or 'Postgraduate'.")

    # Convert to list of dictionaries for pandas
    data_dicts = [dict(row) for row in data]
    df = pd.DataFrame(data_dicts)
    logger.info(f"Retrieved {len(df)} enrollment records")
    return df


# Context manager for application lifecycle
@asynccontextmanager
async def database_lifecycle():
    """Context manager for proper database initialization and cleanup"""
    try:
        await db_manager.init_pool()
        logger.info("Database connection pool initialized")
        yield db_manager
    finally:
        await db_manager.close_pool()
        logger.info("Database connection pool closed")

