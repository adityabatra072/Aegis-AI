"""
Pytest configuration and shared fixtures
"""

import pytest
import os

# Set test environment variables
os.environ['DATABASE_URL'] = os.getenv(
    'TEST_DATABASE_URL',
    'postgresql://aegis_user:aegis_secure_pass_2024@localhost:5432/aegis_db'
)
