async def fetch_student_data(conn, faculty: str = None):
    query = "SELECT session, type, count FROM student"
    if faculty:
        query += " WHERE faculty = $1"
        return await conn.fetch(query, faculty)
    return await conn.fetch(query)

async def fetch_staff_data(conn, faculty: str = None):
    query = "SELECT session, position, count FROM academic_staff"
    if faculty:
        query += " WHERE faculty = $1"
        return await conn.fetch(query, faculty)
    return await conn.fetch(query)
