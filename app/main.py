from fastapi import FastAPI # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.responses import HTMLResponse # type: ignore
from app.charts.home_charts import (
    generate_staff_donut_chart,
    generate_student_donut_chart,
    generate_staff_trend_chart,
    generate_student_trend_chart
)
import pandas as pd # type: ignore
from app.db.database import (
    get_student_dataframe,
    get_staff_dataframe
)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development. Restrict this in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load data






@app.get("/charts/staff-donut", response_class=HTMLResponse)
async def staff_donut_chart(session: str = "2023/2024"):
    df_staff = await get_staff_dataframe()
    # Generate the chart HTML
    chart_html = generate_staff_donut_chart(df_staff, session)
    # Return only the raw chart HTML
    return chart_html

@app.get("/charts/student-donut", response_class=HTMLResponse)
async def student_donut_chart(session: str = "2023/2024"):
    df_students = await get_student_dataframe()
    # Generate the chart HTML
    chart_html = generate_student_donut_chart(df_students, session)
    # Return only the raw chart HTML
    return chart_html

@app.get("/charts/staff-trend", response_class=HTMLResponse)
async def staff_trend_chart():
    df_staff = await get_staff_dataframe()
    # Generate the chart HTML
    chart_html = generate_staff_trend_chart(df_staff)
    # Return only the raw chart HTML
    return chart_html

@app.get("/charts/student-trend", response_class=HTMLResponse)
async def student_trend_chart():
    df_students = await get_student_dataframe()
    # Generate the chart HTML
    chart_html = generate_student_trend_chart(df_students)
    # Return only the raw chart HTML
    return chart_html
