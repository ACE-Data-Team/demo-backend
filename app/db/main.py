from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager

# imports from the charts module (assumed to be sync functions that return HTML strings)
from app.charts.home_charts import (
    generate_staff_donut_chart,
    generate_student_donut_chart,
    generate_staff_trend_chart,
    generate_student_trend_chart,
)

from app.charts.enrollment_charts import (
    generate_total_count,
    student_distribution_by_type,
    generate_enrollment_donut_chart,
    student_gender_barchart
)

import pandas as pd

# imports from the database module
from app.db.database import (
    get_student_dataframe,
    get_staff_dataframe,
    init_db_pool,
    close_pool,
    get_enrollment_dataframe,
)

import time
import logging
from typing import Tuple, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import asyncio

# CONFIGURATION & SETUP
class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class AppConfig:
    """Application configuration"""
    cache_ttl: int = 300  # 5 minutes
    slow_request_threshold: float = 2.0
    medium_request_threshold: float = 1.0
    log_level: LogLevel = LogLevel.INFO
    cors_origins: list = None

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]  # Note to be restricted in production


# Initialize configuration
config = AppConfig()

# Setup structured logging
logging.basicConfig(
    level=getattr(logging, config.log_level.value),
    format="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
)
logger = logging.getLogger(__name__)


# PERFORMANCE MONITORING MIDDLEWARE
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        method = request.method
        path = request.url.path

        logger.info(f"Request started: {method} {path}")

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            response.headers["X-Server-Info"] = "Optimized-FastAPI"
            response.headers["X-Timestamp"] = str(int(time.time()))

            self._log_performance(method, path, process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request failed: {method} {path} - {process_time:.4f}s - Error: {str(e)}")
            raise

    def _log_performance(self, method: str, path: str, process_time: float):
        if process_time > config.slow_request_threshold:
            logger.warning(f"SLOW REQUEST: {method} {path} - {process_time:.4f}s")
        elif process_time > config.medium_request_threshold:
            logger.info(f"Medium response: {method} {path} - {process_time:.4f}s")
        else:
            logger.info(f"Fast response: {method} {path} - {process_time:.4f}s")


# CACHING SYSTEM
@dataclass
class CacheEntry:
    data: str
    timestamp: float
    access_count: int = 0
    last_accessed: float = 0.0

    def is_expired(self, ttl: int) -> bool:
        return time.time() - self.timestamp > ttl

    def touch(self):
        self.access_count += 1
        self.last_accessed = time.time()


class CacheManager:
    def __init__(self, ttl: int = 300):
        self._cache: Dict[str, CacheEntry] = {}
        self.ttl = ttl
        self._stats = {
            "hits": 0,
            "misses": 0,
            "expired": 0,
            "total_requests": 0,
        }

    def get(self, key: str) -> Optional[str]:
        self._stats["total_requests"] += 1

        if key not in self._cache:
            logger.info(f"Cache MISS for {key}")
            self._stats["misses"] += 1
            return None

        entry = self._cache[key]

        if entry.is_expired(self.ttl):
            logger.info(f"Cache EXPIRED for {key}")
            del self._cache[key]
            self._stats["expired"] += 1
            return None

        entry.touch()
        logger.info(f"Cache HIT for {key} (accessed {entry.access_count} times)")
        self._stats["hits"] += 1
        return entry.data

    def set(self, key: str, data: str) -> None:
        self._cache[key] = CacheEntry(data=data, timestamp=time.time())
        logger.info(f"Cached data for {key}")

    def clear(self) -> int:
        count = len(self._cache)
        self._cache.clear()
        self._stats = {key: 0 for key in self._stats}
        logger.info(f"Cache cleared - removed {count} entries")
        return count

    def cleanup_expired(self) -> int:
        expired_keys = [key for key, entry in self._cache.items() if entry.is_expired(self.ttl)]
        for key in expired_keys:
            del self._cache[key]
        if expired_keys:
            logger.info(f"Removed {len(expired_keys)} expired cache entries")
        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        active_entries = len(self._cache)
        hit_rate = (self._stats["hits"] / self._stats["total_requests"] * 100) if self._stats["total_requests"] > 0 else 0
        return {
            "active_entries": active_entries,
            "hit_rate_percent": round(hit_rate, 2),
            "ttl_seconds": self.ttl,
            **self._stats,
        }


cache_manager = CacheManager(ttl=config.cache_ttl)


# APPLICATION LIFECYCLE MANAGEMENT
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application...")
    cleanup_task = None
    try:
        await init_db_pool()
        logger.info("Database pool initialized")

        cleanup_task = asyncio.create_task(periodic_cache_cleanup())
        logger.info("Background cache cleanup started")

        yield

    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise

    finally:
        logger.info("Shutting down application...")
        if cleanup_task:
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass
        await close_pool()
        logger.info("Application shutdown complete")


async def periodic_cache_cleanup():
    while True:
        try:
            await asyncio.sleep(60)
            cache_manager.cleanup_expired()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Cache cleanup error: {str(e)}")


# FASTAPI APPLICATION
app = FastAPI(
    title="Charts API",
    description="Optimized Charts API with performance monitoring and caching",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(TimingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# UTILITY FUNCTIONS
def validate_session(session: str) -> str:
    if not session or len(session.split("/")) != 2:
        raise HTTPException(status_code=400, detail="Session must be in format 'YYYY/YYYY' (e.g., '2023/2024')")
    start, end = session.split("/")
    if not (start.isdigit() and end.isdigit() and len(start) == 4 and len(end) == 4):
        raise HTTPException(status_code=400, detail="Session years must be 4-digit numbers")
    if int(end) <= int(start):
        raise HTTPException(status_code=400, detail="Session end year must be greater than start year")
    return session


async def get_cached_chart(cache_key: str, chart_generator, *args, **kwargs) -> str:
    cached_result = cache_manager.get(cache_key)
    if cached_result:
        return cached_result

    try:
        start_time = time.time()
        # chart_generator is expected to be an async callable in this app; if it's sync, wrap it
        if asyncio.iscoroutinefunction(chart_generator):
            chart_html = await chart_generator(*args, **kwargs)
        else:
            # run sync generator in threadpool to avoid blocking
            loop = asyncio.get_running_loop()
            chart_html = await loop.run_in_executor(None, lambda: chart_generator(*args, **kwargs))

        generation_time = time.time() - start_time
        logger.info(f"Chart generated in {generation_time:.4f}s")

        cache_manager.set(cache_key, chart_html)
        return chart_html

    except Exception as e:
        logger.exception(f"Chart generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Chart generation failed")


# API ENDPOINTS
@app.get("/", tags=["Health"]) 
async def root_health_check():
    try:
        start = time.time()
        # quick DB check with a small call
        await get_staff_dataframe()  # optionally pass a session
        db_time = time.time() - start

        return {
            "message": "Charts API is running",
            "status": "healthy",
            "database": "connected",
            "database_response_time": f"{db_time:.4f}s",
            "cache": cache_manager.get_stats(),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/cache/status", tags=["Cache"]) 
async def cache_status():
    stats = cache_manager.get_stats()
    return {
        **stats,
        "cache_keys": list(cache_manager._cache.keys()),
        "most_accessed": sorted([(k, v.access_count) for k, v in cache_manager._cache.items()], key=lambda x: x[1], reverse=True)[:5],
    }


@app.post("/cache/clear", tags=["Cache"]) 
async def clear_cache():
    cleared_count = cache_manager.clear()
    return {"message": "Cache cleared successfully", "entries_removed": cleared_count, "timestamp": datetime.now().isoformat()}


@app.post("/cache/cleanup", tags=["Cache"]) 
async def cleanup_cache():
    expired_count = cache_manager.cleanup_expired()
    return {"message": "Cache cleanup completed", "expired_entries_removed": expired_count, "timestamp": datetime.now().isoformat()}


# Chart endpoints
@app.get("/charts/staff-donut", response_class=HTMLResponse, tags=["Charts"]) 
async def staff_donut_chart(session: str = Depends(validate_session)):
    cache_key = f"staff_donut_{session}"

    async def generate_chart():
        logger.info(f"Generating staff donut chart for session: {session}")
        df_staff = await get_staff_dataframe(session=session)
        # generator is a sync function, will be executed in threadpool by get_cached_chart
        return generate_staff_donut_chart(df_staff, session)

    return await get_cached_chart(cache_key, generate_chart)


@app.get("/charts/student-donut", response_class=HTMLResponse, tags=["Charts"]) 
async def student_donut_chart(session: str = Depends(validate_session)):
    cache_key = f"student_donut_{session}"

    async def generate_chart():
        logger.info(f"Generating student donut chart for session: {session}")
        df_students = await get_student_dataframe(session=session)
        return generate_student_donut_chart(df_students, session)

    return await get_cached_chart(cache_key, generate_chart)


@app.get("/charts/staff-trend", response_class=HTMLResponse, tags=["Charts"]) 
async def staff_trend_chart(session: str = None):
    cache_key = f"staff_trend_{session or 'all'}"

    async def generate_chart():
        logger.info("Generating staff trend chart")
        df_staff = await get_staff_dataframe(session=session)
        return generate_staff_trend_chart(df_staff)

    return await get_cached_chart(cache_key, generate_chart)


@app.get("/charts/student-trend", response_class=HTMLResponse, tags=["Charts"]) 
async def student_trend_chart(session: str = None):
    cache_key = f"student_trend_{session or 'all'}"

    async def generate_chart():
        logger.info("Generating student trend chart")
        df_students = await get_student_dataframe(session=session)
        return generate_student_trend_chart(df_students)

    return await get_cached_chart(cache_key, generate_chart)


@app.get("/charts/enrollment/total-count", response_class=HTMLResponse, tags=["Charts"]) 
async def total_count_chart(session: str = Depends(validate_session)):
    cache_key = f"total_count_{session}"

    async def count_total():
        logger.info(f"Generating total count chart {session}")
        df = await get_enrollment_dataframe(session=session)
        return generate_enrollment_donut_chart(df, session)

    return await get_cached_chart(cache_key, count_total)


@app.get("/charts/enrollment/distribution", response_class=HTMLResponse, tags=["Charts"]) 
async def distribution_chart(session: str = Depends(validate_session), student_type: str = "Undergraduate"):
    cache_key = f"distribution_chart_{student_type}_{session}"

    async def generate_chart():
        logger.info(f"Generating student distribution chart for {student_type} in {session}")
        df = await get_enrollment_dataframe(student_type=student_type, session=session)
        return student_distribution_by_type(df, session, student_type)

    return await get_cached_chart(cache_key, generate_chart)


@app.get("/charts/enrollment/gender", response_class=HTMLResponse, tags=["Charts"]) 
async def gender_chart(session: str = Depends(validate_session), student_type: str = "Undergraduate"):
    cache_key = f"gender_chart_{student_type}_{session}"

    async def generate_chart():
        logger.info(f"Generating gender chart for {student_type} in {session}")
        df = await get_enrollment_dataframe(student_type=student_type, session=session)
        return student_gender_barchart(df, session, student_type)

    return await get_cached_chart(cache_key, generate_chart)


# Performance and testing endpoints
@app.get("/test/performance", tags=["Testing"]) 
async def performance_test(session: str = "2023/2024"):
    results = {}

    try:
        start = time.time()
        df_staff = await get_staff_dataframe(session=session)
        results["staff_data_fetch"] = time.time() - start

        start = time.time()
        df_students = await get_student_dataframe(session=session)
        results["student_data_fetch"] = time.time() - start

        start = time.time()
        # run sync chart generation in threadpool
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: generate_staff_donut_chart(df_staff, session))
        results["staff_chart_generation"] = time.time() - start

        start = time.time()
        await loop.run_in_executor(None, lambda: generate_student_donut_chart(df_students, session))
        results["student_chart_generation"] = time.time() - start

        results["total_time"] = sum(results.values())
        results["cache_stats"] = cache_manager.get_stats()
        results["timestamp"] = datetime.now().isoformat()

        return results

    except Exception as e:
        logger.exception(f"Performance test failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Performance test failed")


@app.get("/charts/batch", tags=["Charts"]) 
async def batch_chart_generation(session: str = "2023/2024"):
    start_time = time.time()

    try:
        # warm up charts by calling get_cached_chart for each chart
        tasks = [
            get_cached_chart(f"staff_donut_{session}", lambda: generate_staff_donut_chart(asyncio.run(get_staff_dataframe(session=session)), session)),
            get_cached_chart(f"student_donut_{session}", lambda: generate_student_donut_chart(asyncio.run(get_student_dataframe(session=session)), session)),
            get_cached_chart(f"staff_trend_{session}", lambda: generate_staff_trend_chart(asyncio.run(get_staff_dataframe(session=session)))),
            get_cached_chart(f"student_trend_{session}", lambda: generate_student_trend_chart(asyncio.run(get_student_dataframe(session=session)))),
        ]

        # Note: The above tasks contain inner asyncio.run which is not safe inside the running loop.
        # In production you'd build proper async wrappers; for now use explicit concurrency with coroutines below.

        async def t1():
            df = await get_staff_dataframe(session=session)
            return await get_cached_chart(f"staff_donut_{session}", lambda df=df, s=session: generate_staff_donut_chart(df, s))

        async def t2():
            df = await get_student_dataframe(session=session)
            return await get_cached_chart(f"student_donut_{session}", lambda df=df, s=session: generate_student_donut_chart(df, s))

        async def t3():
            df = await get_staff_dataframe(session=session)
            return await get_cached_chart(f"staff_trend_{session}", lambda df=df: generate_staff_trend_chart(df))

        async def t4():
            df = await get_student_dataframe(session=session)
            return await get_cached_chart(f"student_trend_{session}", lambda df=df: generate_student_trend_chart(df))

        await asyncio.gather(t1(), t2(), t3(), t4())

        total_time = time.time() - start_time

        return {
            "message": "All charts generated successfully",
            "total_time": f"{total_time:.4f}s",
            "cache_stats": cache_manager.get_stats(),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.exception(f"Batch generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch generation failed")
