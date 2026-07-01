"""Shared pytest fixtures."""

import asyncio

import pytest


@pytest.fixture(scope="session", autouse=True)
def initialize_database() -> None:
    """Ensure tables exist and fixture sessions are seeded before API tests."""
    from home_tutor.models.database import init_db

    asyncio.run(init_db())
