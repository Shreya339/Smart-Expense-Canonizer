"""
Shared pytest configuration.

This file sets up reusable fixtures that can be used across
unit tests and integration tests.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="module")
def client():
    """
    Provides a FastAPI test client.

    This allows us to call API endpoints like /classify
    without running a real server.
    """
    return TestClient(app)
