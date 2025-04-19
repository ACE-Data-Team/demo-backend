from fastapi import FastAPI
from app.routes import staff, students

app = FastAPI()
app.include_router(staff.router, prefix="/staff", tags=["staff"])
app.include_router(students.router, prefix="/students", tags=["students"])  

@app.get("/")
async def root():
    return {"message": "Welcome to the OAUOIR!"}