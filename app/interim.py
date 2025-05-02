from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
import pandas as pd

app = FastAPI()
router = APIRouter(prefix="/api")

# Dummy data placeholders
df_staff = pd.DataFrame()  # replace with your actual dataframe
df_students = pd.DataFrame()

@router.get("/academic-staff-count")
async def get_academic_staff_count():
    """Total count of academic staff."""
    total_count = len(df_staff)
    return {"academic_staff_count": total_count}


@router.get("/student-distribution-by-type/2023-2024")
async def get_student_distribution():
    """Distribution of students by type (e.g., Undergraduate, Postgraduate) for 2023/2024."""
    filtered = df_students[df_students['session'] == '2023/2024']
    distribution = filtered['type'].value_counts().to_dict()
    return {"distribution": distribution}


@router.get("/academic-staff-growth-and-positions")
async def get_academic_staff_growth():
    """Trend of academic staff growth over time and by position."""
    growth = (
        df_staff.groupby(['session', 'position'])
        .size()
        .reset_index(name='count')
        .to_dict(orient="records")
    )
    return {"staff_growth_by_position": growth}


@router.get("/student-population-trend")
async def get_student_population_trend():
    """Trend of student population over time by type."""
    trend = (
        df_students.groupby(['session', 'type'])
        .size()
        .reset_index(name='count')
        .to_dict(orient="records")
    )
    return {"student_population_trend": trend}


app.include_router(router)









from db import database
from db import queries
