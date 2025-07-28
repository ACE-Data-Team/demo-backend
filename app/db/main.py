from fastapi import FastAPI, Request, HTTPException, Depends # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.responses import HTMLResponse # type: ignore
from starlette.middleware.base import BaseHTTPMiddleware # type: ignore
from contextlib import asynccontextmanager

# imports from the charts module
from app.charts.home_charts import (
    generate_staff_donut_chart,
    generate_student_donut_chart,
    generate_staff_trend_chart,
    generate_student_trend_chart
)

import pandas as pd # type: ignore

# imports from the database module
from app.db.database import (
    get_student_dataframe,
    get_staff_dataframe,
    init_db_pool,
    close_pool
)

import time
import logging
from typing import Tuple, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
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
            self.cors_origins = ["*"]  # To be Restrict in production

# Initialize configuration
config = AppConfig()

# Setup structured logging
logging.basicConfig(
    level=getattr(logging, config.log_level.value),
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

# PERFORMANCE MONITORING MIDDLEWARE
class TimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track request processing time and add performance headers.
    Logs slow requests for monitoring.
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        method = request.method
        path = request.url.path
        
        # Log request start
        logger.info(f" Request started: {method} {path}")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Add performance headers
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            response.headers["X-Server-Info"] = "Optimized-FastAPI"
            response.headers["X-Timestamp"] = str(int(time.time()))
            
            # Log with appropriate level based on performance
            self._log_performance(method, path, process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f" Request failed: {method} {path} - {process_time:.4f}s - Error: {str(e)}")
            raise
    
    def _log_performance(self, method: str, path: str, process_time: float):
        """Log performance with appropriate level"""
        if process_time > config.slow_request_threshold:
            logger.warning(f" SLOW REQUEST: {method} {path} - {process_time:.4f}s")
        elif process_time > config.medium_request_threshold:
            logger.info(f" Medium response: {method} {path} - {process_time:.4f}s")
        else:
            logger.info(f" Fast response: {method} {path} - {process_time:.4f}s")

# CACHING SYSTEM 
@dataclass
class CacheEntry:
    """ Cache entry with metadata """
    data: str
    timestamp: float
    access_count: int = 0
    last_accessed: float = 0
    
    def is_expired(self, ttl: int) -> bool:
        """Check if cache entry is expired"""
        return time.time() - self.timestamp > ttl
    
    def touch(self):
        """Update access statistics"""
        self.access_count += 1
        self.last_accessed = time.time()

class CacheManager:
    """ Cache manager with statistics and cleanup """
    
    def __init__(self, ttl: int = 300):
        self._cache: Dict[str, CacheEntry] = {}
        self.ttl = ttl
        self._stats = {
            'hits': 0,
            'misses': 0,
            'expired': 0,
            'total_requests': 0
        }
    
    def get(self, key: str) -> Optional[str]:
        """Get data from cache with statistics tracking"""
        self._stats['total_requests'] += 1
        
        if key not in self._cache:
            logger.info(f" Cache MISS for {key}")
            self._stats['misses'] += 1
            return None
        
        entry = self._cache[key]
        
        if entry.is_expired(self.ttl):
            logger.info(f" Cache EXPIRED for {key}")
            del self._cache[key]
            self._stats['expired'] += 1
            return None
        
        # Update access statistics
        entry.touch()
        logger.info(f" Cache HIT for {key} (accessed {entry.access_count} times)")
        self._stats['hits'] += 1
        return entry.data
    
    def set(self, key: str, data: str) -> None:
        """Set data in cache"""
        self._cache[key] = CacheEntry(data=data, timestamp=time.time())
        logger.info(f" Cached data for {key}")
    
    def clear(self) -> int:
        """Clear all cache entries"""
        count = len(self._cache)
        self._cache.clear()
        self._stats = {key: 0 for key in self._stats}
        logger.info(f" Cache cleared - removed {count} entries")
        return count
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired(self.ttl)
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f" Removed {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        active_entries = len(self._cache)
        hit_rate = (self._stats['hits'] / self._stats['total_requests'] * 100) if self._stats['total_requests'] > 0 else 0
        
        return {
            'active_entries': active_entries,
            'hit_rate_percent': round(hit_rate, 2),
            'ttl_seconds': self.ttl,
            **self._stats
        }

# Initialize cache manager
cache_manager = CacheManager(ttl=config.cache_ttl)

# APPLICATION LIFECYCLE MANAGEMENT 
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info(" Starting up application...")
    try:
        await init_db_pool()
        logger.info(" Database pool initialized")
        
        # Start background cache cleanup task
        cleanup_task = asyncio.create_task(periodic_cache_cleanup())
        logger.info(" Background cache cleanup started")
        
        logger.info(" Application startup complete")
        yield
        
    except Exception as e:
        logger.error(f" Startup failed: {str(e)}")
        raise
    finally:
        # Shutdown
        logger.info(" Shutting down application...")
        cleanup_task.cancel()
        await close_pool()
        logger.info(" Application shutdown complete")

async def periodic_cache_cleanup():
    """Background task to clean up expired cache entries"""
    while True:
        try:
            await asyncio.sleep(60)  # Run every minute
            cache_manager.cleanup_expired()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f" Cache cleanup error: {str(e)}")

# FASTAPI APPLICATION
app = FastAPI(
    title="Charts API",
    description="Optimized Charts API with performance monitoring and caching",
    version="2.0.0",
    lifespan=lifespan
)

# Add middlewares
app.add_middleware(TimingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# UTILITY FUNCTIONS 
def validate_session(session: str) -> str:
    """Validate session format"""
    if not session or len(session.split('/')) != 2:
        raise HTTPException(
            status_code=400,
            detail="Session must be in format 'YYYY/YYYY' (e.g., '2023/2024')"
        )
    return session

async def get_cached_chart(cache_key: str, chart_generator, *args, **kwargs) -> str:
    """Generic cached chart getter with error handling"""
    # Try cache first
    cached_result = cache_manager.get(cache_key)
    if cached_result:
        return cached_result
    
    # Cache miss - generate chart
    try:
        start_time = time.time()
        chart_html = await chart_generator(*args, **kwargs)
        generation_time = time.time() - start_time
        
        logger.info(f" Chart generated in {generation_time:.4f}s")
        
        # Cache the result
        cache_manager.set(cache_key, chart_html)
        return chart_html
        
    except Exception as e:
        logger.error(f" Chart generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Chart generation failed")

# API ENDPOINTS 

# Health check and status endpoints
@app.get("/", tags=["Health"])
async def root_health_check():
    """Detailed health check"""
    try:
        # Quick database check
        start = time.time()
        await get_staff_dataframe()
        db_time = time.time() - start
        
        return {
            "message": "Charts API is running",
            "status": "healthy",
            "database": "connected",
            "database_response_time": f"{db_time:.4f}s",
            "cache": cache_manager.get_stats(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f" Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.get("/cache/status", tags=["Cache"])
async def cache_status():
    """Get detailed cache statistics"""
    stats = cache_manager.get_stats()
    return {
        **stats,
        "cache_keys": list(cache_manager._cache.keys()),
        "most_accessed": sorted(
            [(k, v.access_count) for k, v in cache_manager._cache.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]  # Top 5 most accessed
    }

@app.post("/cache/clear", tags=["Cache"])
async def clear_cache():
    """Clear all cache entries"""
    cleared_count = cache_manager.clear()
    return {
        "message": f"Cache cleared successfully",
        "entries_removed": cleared_count,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/cache/cleanup", tags=["Cache"])
async def cleanup_cache():
    """Manually trigger cache cleanup"""
    expired_count = cache_manager.cleanup_expired()
    return {
        "message": "Cache cleanup completed",
        "expired_entries_removed": expired_count,
        "timestamp": datetime.now().isoformat()
    }

# Chart endpoints
@app.get("/charts/staff-donut", response_class=HTMLResponse, tags=["Charts"])
async def staff_donut_chart(session: str = Depends(validate_session)):
    """Generate staff donut chart for specified session"""
    cache_key = f"staff_donut_{session}"
    
    async def generate_chart():
        logger.info(f" Generating staff donut chart for session: {session}")
        df_staff = await get_staff_dataframe()
        return generate_staff_donut_chart(df_staff, session)
    
    return await get_cached_chart(cache_key, generate_chart)

@app.get("/charts/student-donut", response_class=HTMLResponse, tags=["Charts"])
async def student_donut_chart(session: str = Depends(validate_session)):
    """Generate student donut chart for specified session"""
    cache_key = f"student_donut_{session}"
    
    async def generate_chart():
        logger.info(f" Generating student donut chart for session: {session}")
        df_students = await get_student_dataframe()
        return generate_student_donut_chart(df_students, session)
    
    return await get_cached_chart(cache_key, generate_chart)

@app.get("/charts/staff-trend", response_class=HTMLResponse, tags=["Charts"])
async def staff_trend_chart():
    """Generate staff trend chart"""
    cache_key = "staff_trend"
    
    async def generate_chart():
        logger.info(" Generating staff trend chart")
        df_staff = await get_staff_dataframe()
        return generate_staff_trend_chart(df_staff)
    
    return await get_cached_chart(cache_key, generate_chart)

@app.get("/charts/student-trend", response_class=HTMLResponse, tags=["Charts"])
async def student_trend_chart():
    """Generate student trend chart"""
    cache_key = "student_trend"
    
    async def generate_chart():
        logger.info(" Generating student trend chart")
        df_students = await get_student_dataframe()
        return generate_student_trend_chart(df_students)
    
    return await get_cached_chart(cache_key, generate_chart)

# Performance and testing endpoints
@app.get("/test/performance", tags=["Testing"])
async def performance_test():
    """Comprehensive performance test endpoint"""
    results = {}
    
    try:
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
        
        # Calculate totals
        results['total_time'] = sum(results.values())
        results['cache_stats'] = cache_manager.get_stats()
        results['timestamp'] = datetime.now().isoformat()
        
        return results
        
    except Exception as e:
        logger.error(f"Performance test failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Performance test failed")

@app.get("/charts/batch", tags=["Charts"])
async def batch_chart_generation():
    """Generate all charts at once for warming up cache"""
    start_time = time.time()
    
    try:
        # Generate all charts concurrently
        tasks = [
            staff_donut_chart("2023/2024"),
            student_donut_chart("2023/2024"),
            staff_trend_chart(),
            student_trend_chart()
        ]
        
        await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        return {
            "message": "All charts generated successfully",
            "total_time": f"{total_time:.4f}s",
            "cache_stats": cache_manager.get_stats(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f" Batch generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch generation failed")