from fastapi import FastAPI, Request # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.responses import HTMLResponse # type: ignore
from starlette.middleware.base import BaseHTTPMiddleware # type: ignore
from app.charts.home_charts import (
    generate_staff_donut_chart,
    generate_student_donut_chart,
    generate_staff_trend_chart,
    generate_student_trend_chart
)
import pandas as pd # type: ignore
from app.db.database import (
    get_student_dataframe,
    get_staff_dataframe,
    init_db_pool,
    close_pool
)
import time
import logging
from typing import Tuple, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Charts API", description="Optimized Charts API with performance monitoring")

# Performance monitoring middleware
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request start
        logger.info(f" Request started: {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add timing header to response
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        response.headers["X-Server-Info"] = "Optimized-FastAPI"
        
        # Log request completion with timing
        if process_time > 2.0:
            logger.warning(f" SLOW REQUEST: {request.method} {request.url.path} - {process_time:.4f}s")
        elif process_time > 1.0:
            logger.info(f"  Medium response: {request.method} {request.url.path} - {process_time:.4f}s")
        else:
            logger.info(f" Fast response: {request.method} {request.url.path} - {process_time:.4f}s")
        
        return response

# Add timing middleware
app.add_middleware(TimingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development. Restrict this in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory cache with TTL
_cache = {}
CACHE_TTL = 300  # 5 minutes cache

def get_from_cache(cache_key: str) -> Optional[str]:
    """Get data from cache if it exists and hasn't expired"""
    current_time = time.time()
    
    if cache_key in _cache:
        data, timestamp = _cache[cache_key]
        if current_time - timestamp < CACHE_TTL:
            logger.info(f" Cache HIT for {cache_key}")
            return data
        else:
            # Remove expired entry
            del _cache[cache_key]
            logger.info(f" Cache EXPIRED for {cache_key}")
    
    logger.info(f" Cache MISS for {cache_key}")
    return None

def set_cache(cache_key: str, data: str) -> None:
    """Set data in cache with current timestamp"""
    _cache[cache_key] = (data, time.time())
    logger.info(f" Cached data for {cache_key}")

def time_chart_generation(chart_name: str):
    """Decorator to time chart generation"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f" Chart '{chart_name}' generated in {duration:.4f}s")
            return result
        return wrapper
    return decorator

# Startup event to initialize database pool
@app.on_event("startup")
async def startup_event():
    logger.info(" Starting up application...")
    await init_db_pool()
    logger.info(" Application startup complete")

# Shutdown event to close database pool
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")
    await close_pool()
    logger.info(" Application shutdown complete")

# Root endpoint for health check
@app.get("/")
async def root():
    return {
        "message": "Charts API is running", 
        "status": "healthy",
        "cache_size": len(_cache),
        "timestamp": time.time()
    }

# Cache status endpoint
@app.get("/cache/status")
async def cache_status():
    current_time = time.time()
    active_entries = 0
    expired_entries = 0
    
    for key, (data, timestamp) in _cache.items():
        if current_time - timestamp < CACHE_TTL:
            active_entries += 1
        else:
            expired_entries += 1
    
    return {
        "total_entries": len(_cache),
        "active_entries": active_entries,
        "expired_entries": expired_entries,
        "cache_ttl_seconds": CACHE_TTL
    }

# Clear cache endpoint (useful for testing)
@app.post("/cache/clear")
async def clear_cache():
    global _cache
    old_size = len(_cache)
    _cache.clear()
    logger.info(f" Cache cleared - removed {old_size} entries")
    return {"message": f"Cache cleared successfully - removed {old_size} entries"}

@app.get("/charts/staff-donut", response_class=HTMLResponse)
async def staff_donut_chart(session: str = "2023/2024"):
    cache_key = f"staff_donut_{session}"
    
    # Try to get from cache first
    cached_result = get_from_cache(cache_key)
    if cached_result:
        return cached_result
    
    # Cache miss - fetch data and generate chart
    logger.info(f" Generating staff donut chart for session: {session}")
    df_staff = await get_staff_dataframe()
    
    # Time the chart generation
    chart_start = time.time()
    chart_html = generate_staff_donut_chart(df_staff, session)
    chart_duration = time.time() - chart_start
    logger.info(f" Staff donut chart generated in {chart_duration:.4f}s")
    
    # Cache the result
    set_cache(cache_key, chart_html)
    
    return chart_html

@app.get("/charts/student-donut", response_class=HTMLResponse)
async def student_donut_chart(session: str = "2023/2024"):
    cache_key = f"student_donut_{session}"
    
    # Try to get from cache first
    cached_result = get_from_cache(cache_key)
    if cached_result:
        return cached_result
    
    # Cache miss - fetch data and generate chart
    logger.info(f" Generating student donut chart for session: {session}")
    df_students = await get_student_dataframe()
    
    # Time the chart generation
    chart_start = time.time()
    chart_html = generate_student_donut_chart(df_students, session)
    chart_duration = time.time() - chart_start
    logger.info(f" Student donut chart generated in {chart_duration:.4f}s")
    
    # Cache the result
    set_cache(cache_key, chart_html)
    
    return chart_html

@app.get("/charts/staff-trend", response_class=HTMLResponse)
async def staff_trend_chart():
    cache_key = "staff_trend"
    
    # Try to get from cache first
    cached_result = get_from_cache(cache_key)
    if cached_result:
        return cached_result
    
    # Cache miss - fetch data and generate chart
    logger.info(" Generating staff trend chart")
    df_staff = await get_staff_dataframe()
    
    # Time the chart generation
    chart_start = time.time()
    chart_html = generate_staff_trend_chart(df_staff)
    chart_duration = time.time() - chart_start
    logger.info(f" Staff trend chart generated in {chart_duration:.4f}s")
    
    # Cache the result
    set_cache(cache_key, chart_html)
    
    return chart_html

@app.get("/charts/student-trend", response_class=HTMLResponse)
async def student_trend_chart():
    cache_key = "student_trend"
    
    # Try to get from cache first
    cached_result = get_from_cache(cache_key)
    if cached_result:
        return cached_result
    
    # Cache miss - fetch data and generate chart
    logger.info(" Generating student trend chart")
    df_students = await get_student_dataframe()
    
    # Time the chart generation
    chart_start = time.time()
    chart_html = generate_student_trend_chart(df_students)
    chart_duration = time.time() - chart_start
    logger.info(f" Student trend chart generated in {chart_duration:.4f}s")
    
    # Cache the result
    set_cache(cache_key, chart_html)
    
    return chart_html

# Performance testing endpoints
@app.get("/test/performance")
async def performance_test():
    """Quick performance test endpoint"""
    results = {}
    
    # Test database operations
    start = time.time()
    df_staff = await get_staff_dataframe()
    results['staff_data_fetch'] = time.time() - start
    
    start = time.time()
    df_students = await get_student_dataframe()
    results['student_data_fetch'] = time.time() - start
    
    # Test chart generation (without caching)
    start = time.time()
    generate_staff_donut_chart(df_staff, "2023/2024")
    results['staff_chart_generation'] = time.time() - start
    
    start = time.time()
    generate_student_donut_chart(df_students, "2023/2024")
    results['student_chart_generation'] = time.time() - start
    
    results['total_time'] = sum(results.values())
    results['cache_entries'] = len(_cache)
    
    return results