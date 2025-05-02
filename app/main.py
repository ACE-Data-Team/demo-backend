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
df_staff = pd.read_csv('/home/prechy/Dev/ace_projects/demo-backend/app/demo/academic_staff_data.csv')
df_students = pd.read_csv('/home/prechy/Dev/ace_projects/demo-backend/app/demo/student_data.csv')

@app.get("/charts/staff-donut", response_class=HTMLResponse)
async def staff_donut_chart(session: str = "2023/2024"):
    # Generate the chart HTML
    chart_html = generate_staff_donut_chart(df_staff, session)
    # Return only the raw chart HTML
    return chart_html

@app.get("/charts/student-donut", response_class=HTMLResponse)
async def student_donut_chart(session: str = "2023/2024"):
    # Generate the chart HTML
    chart_html = generate_student_donut_chart(df_students, session)
    # Return only the raw chart HTML
    return chart_html

@app.get("/charts/staff-trend", response_class=HTMLResponse)
async def staff_trend_chart():
    # Generate the chart HTML
    chart_html = generate_staff_trend_chart(df_staff)
    # Return only the raw chart HTML
    return chart_html

@app.get("/charts/student-trend", response_class=HTMLResponse)
async def student_trend_chart():
    # Generate the chart HTML
    chart_html = generate_student_trend_chart(df_students)
    # Return only the raw chart HTML
    return chart_html
