def build_query_with_faculty(base_query: str, faculty: str = None):
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
