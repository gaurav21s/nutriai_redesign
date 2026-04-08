import os

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_shared_coordinator


@pytest.fixture(scope="session", autouse=True)
def configure_test_env() -> None:
    os.environ.setdefault("AUTH_DISABLED", "true")
    os.environ.setdefault("ENABLE_CONVEX_PERSISTENCE", "false")
    os.environ.setdefault("RATE_LIMIT_DEFAULT_PER_MINUTE", "2")
    os.environ.setdefault("REQUIRE_SHARED_COORDINATION_IN_PRODUCTION", "false")


@pytest.fixture()
def client() -> TestClient:
    from app.main import create_app

    get_shared_coordinator.cache_clear()
    app = create_app()
    return TestClient(app)
