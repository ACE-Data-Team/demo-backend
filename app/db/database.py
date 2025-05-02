import asyncpg # type: ignore
import os
import pandas as pd # type: ignore
from dotenv import load_dotenv # type: ignore

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("The DATABASE_URL environment variable is not set. Please set it to proceed.")

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

async def close_connection(conn):
    """
    Closes the database connection.
    Args:
        conn (asyncpg.Connection): The connection to be closed.
    """
    await conn.close()

def build_query_with_faculty(base_query: str, faculty: str = None):
    """
    Builds a SQL query with an optional WHERE clause for faculty.
    Args:
        base_query (str): Base SQL query.
        faculty (str, optional): Faculty filter. Defaults to None.
    Returns:
        tuple: SQL query and parameters list.
    """

    if faculty:
        return f"{base_query} WHERE faculty = $1", [faculty]
    return base_query, []


async def fetch_student_data(conn, faculty: str = None):
    base_query = "SELECT session, type, count FROM student"
    query, params = build_query_with_faculty(base_query, faculty)
    return await conn.fetch(query, *params)


async def fetch_staff_data(conn, faculty: str = None):
    base_query = "SELECT session, position, count FROM academic_staff"
    query, params = build_query_with_faculty(base_query, faculty)
    return await conn.fetch(query, *params)


async def get_student_dataframe(faculty: str = None):
    """
    Fetches student data and returns it as a pandas DataFrame.
    Args:
        faculty (str, optional): Faculty filter. Defaults to None.    
    Returns:
        pd.DataFrame: DataFrame containing student data.
    """
    conn = await get_connection()
    try:
        data = await fetch_student_data(conn, faculty)
        # Convert to list of dictionaries for pandas
        data_dicts = [dict(row) for row in data]
        df = pd.DataFrame(data_dicts)
        return df
    finally:
        await close_connection(conn)

async def get_staff_dataframe(faculty: str = None):
    """
    Fetches academic staff data and returns it as a pandas DataFrame. 
    Args:
        faculty (str, optional): Faculty filter. Defaults to None.    
    Returns:
        pd.DataFrame: DataFrame containing academic staff data.
    """
    conn = await get_connection()
    try:
        data = await fetch_staff_data(conn, faculty)
        # Convert to list of dictionaries for pandas
        data_dicts = [dict(row) for row in data]
        df = pd.DataFrame(data_dicts)
        return df
    finally:
        await close_connection(conn)
