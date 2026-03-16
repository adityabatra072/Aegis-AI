"""
Test suite for Aegis-AI Database Layer
"""

import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import DatabaseManager


@pytest.fixture
def db():
    """Fixture to create a database manager instance."""
    db_manager = DatabaseManager()
    yield db_manager
    db_manager.close()


def test_database_initialization():
    """Test that database manager initializes correctly."""
    db = DatabaseManager()
    assert db is not None
    assert db.pool is not None
    db.close()


def test_database_health_check(db):
    """Test database health check."""
    # This will only pass if database is running
    is_healthy = db.health_check()
    assert isinstance(is_healthy, bool)


def test_insert_log(db):
    """Test inserting a log entry."""
    if not db.health_check():
        pytest.skip("Database not available")

    log_id = db.insert_log(
        log_level="INFO",
        source_ip="192.168.1.100",
        message="Test log entry for unit testing"
    )
    assert isinstance(log_id, int)
    assert log_id > 0


def test_insert_log_with_metadata(db):
    """Test inserting a log with metadata."""
    if not db.health_check():
        pytest.skip("Database not available")

    metadata = {"test": True, "source": "unit_test"}
    log_id = db.insert_log(
        log_level="WARNING",
        source_ip="10.0.0.1",
        message="Test log with metadata",
        metadata=metadata
    )
    assert isinstance(log_id, int)


def test_get_unclassified_logs(db):
    """Test retrieving unclassified logs."""
    if not db.health_check():
        pytest.skip("Database not available")

    logs = db.get_unclassified_logs(limit=5)
    assert isinstance(logs, list)
    # Each log should have required fields
    for log in logs:
        assert 'id' in log
        assert 'timestamp' in log
        assert 'message' in log
        assert 'source_ip' in log


def test_update_classification(db):
    """Test updating log classification."""
    if not db.health_check():
        pytest.skip("Database not available")

    # First insert a log
    log_id = db.insert_log(
        log_level="ERROR",
        source_ip="45.142.212.61",
        message="SQL injection attempt: ' OR 1=1--"
    )

    # Then update its classification
    db.update_classification(
        log_id=log_id,
        classification="CRITICAL_THREAT",
        is_threat=True,
        metadata={"confidence": 0.95, "attack_type": "SQL_INJECTION"}
    )

    # Verify it's no longer unclassified
    unclassified = db.get_unclassified_logs(limit=1000)
    unclassified_ids = [log['id'] for log in unclassified]
    assert log_id not in unclassified_ids


def test_get_recent_threats(db):
    """Test retrieving recent threats."""
    if not db.health_check():
        pytest.skip("Database not available")

    threats = db.get_recent_threats(hours=24, limit=10)
    assert isinstance(threats, list)
    # Each threat should have required fields
    for threat in threats:
        assert 'id' in threat
        assert 'timestamp' in threat
        assert 'ai_classification' in threat


def test_get_statistics(db):
    """Test retrieving database statistics."""
    if not db.health_check():
        pytest.skip("Database not available")

    stats = db.get_statistics()
    assert isinstance(stats, dict)
    assert 'total_logs' in stats
    assert 'total_threats' in stats
    assert 'safe_count' in stats
    assert 'suspicious_count' in stats
    assert 'critical_count' in stats
    assert 'unclassified_count' in stats


def test_connection_pool_management(db):
    """Test that connection pool is properly managed."""
    if not db.health_check():
        pytest.skip("Database not available")

    # Simulate multiple concurrent operations
    for _ in range(5):
        db.insert_log(
            log_level="INFO",
            source_ip="127.0.0.1",
            message="Connection pool test"
        )

    # Pool should still be functional
    assert db.health_check()
