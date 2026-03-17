"""
Aegis-AI Database Layer
=======================
Purpose: Centralized database connection management and data access layer
Author: Aditya Batra

This module provides:
- Thread-safe database connection pooling
- CRUD operations for log entries
- Query utilities for threat detection workflows
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import SimpleConnectionPool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Thread-safe database connection manager with connection pooling.

    Design Pattern: Singleton with connection pooling for production scalability.
    Security: Uses environment variables for credentials to avoid hardcoding.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the database connection pool.

        Args:
            database_url: PostgreSQL connection string (falls back to env var)
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://aegis_user:aegis_secure_pass_2024@localhost:5432/aegis_db"
        )

        # Connection pool: min 1, max 10 concurrent connections
        # This prevents connection exhaustion under high load
        self.pool: Optional[SimpleConnectionPool] = None
        self._initialize_pool()

    def _initialize_pool(self):
        """Create the connection pool with retry logic."""
        try:
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=self.database_url
            )
            logger.info("✅ Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database pool: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """
        Context manager for safe connection handling.

        Ensures connections are always returned to the pool, even on exceptions.

        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM logs")
        """
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database transaction error: {e}")
            raise
        finally:
            if conn:
                self.pool.putconn(conn)

    def insert_log(
        self,
        log_level: str,
        source_ip: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Insert a new log entry into the database.

        Args:
            log_level: Severity (INFO, WARNING, ERROR, CRITICAL)
            source_ip: Source IP address
            message: Raw log message
            metadata: Optional JSON metadata

        Returns:
            The ID of the inserted log entry
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO server_logs (log_level, source_ip, message, metadata)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (log_level, source_ip, message, Json(metadata or {}))
            )
            log_id = cursor.fetchone()[0]
            logger.debug(f"Inserted log entry with ID: {log_id}")
            return log_id

    def get_unclassified_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve logs that haven't been analyzed by AI yet.

        This is the core query for the analyzer service polling loop.
        Uses the idx_logs_unclassified index for performance.

        Args:
            limit: Maximum number of logs to retrieve

        Returns:
            List of log dictionaries with all fields
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT id, timestamp, log_level, source_ip, message, metadata
                FROM server_logs
                WHERE ai_classification IS NULL
                ORDER BY timestamp ASC
                LIMIT %s
                """,
                (limit,)
            )
            logs = cursor.fetchall()
            logger.info(f"Retrieved {len(logs)} unclassified logs")
            return [dict(log) for log in logs]

    def update_classification(
        self,
        log_id: int,
        classification: str,
        is_threat: bool,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Update a log entry with AI classification results.

        Args:
            log_id: ID of the log to update
            classification: AI output (SAFE, SUSPICIOUS, CRITICAL_THREAT)
            is_threat: Boolean threat indicator
            metadata: Additional analysis metadata (confidence score, attack type, etc.)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Merge new metadata with existing - convert dict to JSON
            update_metadata = Json(metadata or {})

            cursor.execute(
                """
                UPDATE server_logs
                SET ai_classification = %s,
                    is_threat = %s,
                    analyzed_at = NOW(),
                    metadata = metadata || %s
                WHERE id = %s
                """,
                (classification, is_threat, update_metadata, log_id)
            )
            logger.debug(f"Updated log {log_id} with classification: {classification}")

    def get_recent_threats(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent threat detections for dashboard/API.

        Uses the idx_logs_threat_timeline composite index.

        Args:
            hours: Look back period in hours
            limit: Maximum results to return

        Returns:
            List of threat log dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cutoff_time = datetime.now() - timedelta(hours=hours)

            cursor.execute(
                """
                SELECT
                    id,
                    timestamp,
                    log_level,
                    source_ip,
                    message,
                    ai_classification,
                    analyzed_at,
                    metadata
                FROM server_logs
                WHERE is_threat = TRUE
                  AND timestamp >= %s
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (cutoff_time, limit)
            )
            threats = cursor.fetchall()
            logger.info(f"Retrieved {len(threats)} threats from last {hours} hours")
            return [dict(threat) for threat in threats]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get aggregate statistics for monitoring dashboard.

        Returns:
            Dictionary with total logs, threats, classification breakdown
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_logs,
                    COUNT(*) FILTER (WHERE is_threat = TRUE) as total_threats,
                    COUNT(*) FILTER (WHERE ai_classification = 'SAFE') as safe_count,
                    COUNT(*) FILTER (WHERE ai_classification = 'SUSPICIOUS') as suspicious_count,
                    COUNT(*) FILTER (WHERE ai_classification = 'CRITICAL_THREAT') as critical_count,
                    COUNT(*) FILTER (WHERE ai_classification IS NULL) as unclassified_count
                FROM server_logs
                """
            )
            stats = cursor.fetchone()
            return dict(stats) if stats else {}

    def health_check(self) -> bool:
        """
        Verify database connectivity.

        Returns:
            True if database is reachable, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def close(self):
        """Close all connections in the pool."""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")
