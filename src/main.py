"""
Aegis-AI API Gateway
====================
Purpose: RESTful API for accessing threat intelligence and system monitoring
Author: Aditya Batra

This FastAPI service provides:
- /status endpoint: System health and statistics
- /threats endpoint: Query recent threat detections
- /logs endpoint: Query all logs with filtering
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Aegis-AI Threat Detection API",
    description="AI-powered security threat detection and log analysis system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Database manager will be initialized on startup
db: Optional[DatabaseManager] = None


# Pydantic models for API responses
class ThreatResponse(BaseModel):
    """Response model for threat detection results."""
    id: int = Field(..., description="Unique log entry ID")
    timestamp: datetime = Field(..., description="When the log event occurred")
    log_level: str = Field(..., description="Severity level")
    source_ip: str = Field(..., description="Source IP address")
    message: str = Field(..., description="Raw log message")
    ai_classification: str = Field(..., description="AI classification result")
    analyzed_at: Optional[datetime] = Field(None, description="When AI analysis was performed")
    metadata: dict = Field(default_factory=dict, description="Additional analysis metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "timestamp": "2026-03-17T10:30:00",
                "log_level": "CRITICAL",
                "source_ip": "45.142.212.61",
                "message": "POST /api/login - SQL Injection attempt: ' OR '1'='1",
                "ai_classification": "CRITICAL_THREAT",
                "analyzed_at": "2026-03-17T10:30:05",
                "metadata": {
                    "confidence": 0.95,
                    "attack_type": "SQL_INJECTION",
                    "reasoning": "Detected SQL injection pattern"
                }
            }
        }


class StatisticsResponse(BaseModel):
    """Response model for system statistics."""
    total_logs: int = Field(..., description="Total number of logs in database")
    total_threats: int = Field(..., description="Total number of detected threats")
    safe_count: int = Field(..., description="Number of safe logs")
    suspicious_count: int = Field(..., description="Number of suspicious logs")
    critical_count: int = Field(..., description="Number of critical threats")
    unclassified_count: int = Field(..., description="Number of unclassified logs")
    threat_percentage: float = Field(..., description="Percentage of threats vs total logs")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="System status")
    database: str = Field(..., description="Database connection status")
    timestamp: datetime = Field(..., description="Current server time")


# API Endpoints

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information.
    """
    return {
        "service": "Aegis-AI Threat Detection System",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "threats": "/threats",
            "logs": "/logs",
            "documentation": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        System health status and database connectivity
    """
    db_status = "healthy" if db.health_check() else "unhealthy"

    if db_status == "unhealthy":
        raise HTTPException(status_code=503, detail="Database connection failed")

    return HealthResponse(
        status="healthy",
        database=db_status,
        timestamp=datetime.now()
    )


@app.get("/status", response_model=StatisticsResponse, tags=["Monitoring"])
async def get_status():
    """
    Get system statistics and operational metrics.

    Returns:
        Comprehensive statistics about log processing and threat detection
    """
    try:
        stats = db.get_statistics()

        # Calculate threat percentage
        total = stats.get('total_logs', 0)
        threats = stats.get('total_threats', 0)
        threat_percentage = (threats / total * 100) if total > 0 else 0.0

        return StatisticsResponse(
            total_logs=stats.get('total_logs', 0),
            total_threats=threats,
            safe_count=stats.get('safe_count', 0),
            suspicious_count=stats.get('suspicious_count', 0),
            critical_count=stats.get('critical_count', 0),
            unclassified_count=stats.get('unclassified_count', 0),
            threat_percentage=round(threat_percentage, 2)
        )
    except Exception as e:
        logger.error(f"Failed to fetch statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@app.get("/threats", response_model=List[ThreatResponse], tags=["Threat Intelligence"])
async def get_threats(
    hours: int = Query(24, ge=1, le=168, description="Look back period in hours (1-168)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results to return (1-1000)")
):
    """
    Retrieve recent threat detections.

    This endpoint returns logs classified as SUSPICIOUS or CRITICAL_THREAT
    within the specified time window.

    Args:
        hours: Look back period in hours (default: 24, max: 168 = 1 week)
        limit: Maximum number of results (default: 100, max: 1000)

    Returns:
        List of threat detections with AI analysis results
    """
    try:
        threats = db.get_recent_threats(hours=hours, limit=limit)

        return [
            ThreatResponse(
                id=t['id'],
                timestamp=t['timestamp'],
                log_level=t['log_level'],
                source_ip=t['source_ip'],
                message=t['message'],
                ai_classification=t['ai_classification'],
                analyzed_at=t['analyzed_at'],
                metadata=t['metadata']
            )
            for t in threats
        ]
    except Exception as e:
        logger.error(f"Failed to fetch threats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve threats")


@app.get("/logs", tags=["Log Management"])
async def get_logs(
    classification: Optional[str] = Query(
        None,
        description="Filter by AI classification (SAFE, SUSPICIOUS, CRITICAL_THREAT)"
    ),
    limit: int = Query(50, ge=1, le=500, description="Maximum results to return")
):
    """
    Retrieve logs with optional filtering.

    Args:
        classification: Filter by AI classification
        limit: Maximum number of results

    Returns:
        List of log entries
    """
    try:
        # Build query based on filters
        with db.get_connection() as conn:
            cursor = conn.cursor()

            if classification:
                cursor.execute(
                    """
                    SELECT id, timestamp, log_level, source_ip, message,
                           ai_classification, analyzed_at, metadata
                    FROM server_logs
                    WHERE ai_classification = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                    """,
                    (classification, limit)
                )
            else:
                cursor.execute(
                    """
                    SELECT id, timestamp, log_level, source_ip, message,
                           ai_classification, analyzed_at, metadata
                    FROM server_logs
                    ORDER BY timestamp DESC
                    LIMIT %s
                    """,
                    (limit,)
                )

            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return JSONResponse(content={
                "count": len(logs),
                "logs": logs
            })

    except Exception as e:
        logger.error(f"Failed to fetch logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve logs")


# Exception handlers

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "message": "The requested endpoint does not exist",
            "available_endpoints": ["/health", "/status", "/threats", "/logs"]
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# Startup and shutdown events

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    global db
    logger.info("🚀 Aegis-AI API Gateway starting up...")

    # Initialize database connection
    db = DatabaseManager()

    # Verify database connection
    if db.health_check():
        logger.info("✅ Database connection verified")
    else:
        logger.error("❌ Database connection failed")

    logger.info("✅ API Gateway ready - listening on http://0.0.0.0:8000")
    logger.info("📚 API Documentation: http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    logger.info("🛑 Shutting down API Gateway...")
    if db:
        db.close()
    logger.info("✅ Cleanup complete")


# Entry point for development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
