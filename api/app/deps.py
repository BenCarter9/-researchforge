from __future__ import annotations

import os
from collections.abc import Generator

import anthropic
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.llm.client import ClaudeClient
from app.sec.client import SecClient


def get_db() -> Generator[Session, None, None]:
    """Request-scoped DB session dependency. Overridden in tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_sec_client() -> SecClient:
    """SEC EDGAR client dependency. Overridden with a fake in tests so no
    network access happens during tests."""
    user_agent = os.environ.get("SEC_USER_AGENT", "ResearchForge you@example.com")
    return SecClient(user_agent)


def get_claude_client() -> ClaudeClient:
    """Claude client dependency. The real `anthropic.Anthropic()` client is
    constructed lazily here (only when this dependency is actually called),
    so tests that override this dependency never construct it and never
    need an API key."""
    return ClaudeClient(anthropic.Anthropic())
