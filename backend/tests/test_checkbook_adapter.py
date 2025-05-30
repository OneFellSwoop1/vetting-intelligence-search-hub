import pytest
import asyncio
from app.adapters.checkbook import search_checkbook

@pytest.mark.asyncio
async def test_search_checkbook_returns_list():
    results = await search_checkbook("test")
    assert isinstance(results, list) 