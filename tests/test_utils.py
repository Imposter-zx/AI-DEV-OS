from unittest.mock import AsyncMock

import pytest

from ai_dev_os.utils.error_handling import with_retry
from ai_dev_os.utils.monitoring import setup_structured_logging


@pytest.mark.asyncio
async def test_with_retry_success_on_first_try():
    mock_func = AsyncMock(return_value="success")

    @with_retry(max_retries=3, base_delay=0.1)
    async def my_func():
        return await mock_func()

    result = await my_func()
    assert result == "success"
    assert mock_func.call_count == 1


@pytest.mark.asyncio
async def test_with_retry_success_after_failure():
    mock_func = AsyncMock(side_effect=[ValueError("fail"), "success"])

    @with_retry(max_retries=3, base_delay=0.1)
    async def my_func():
        return await mock_func()

    result = await my_func()
    assert result == "success"
    assert mock_func.call_count == 2


@pytest.mark.asyncio
async def test_with_retry_all_failures():
    mock_func = AsyncMock(side_effect=ValueError("fail"))

    @with_retry(max_retries=3, base_delay=0.1)
    async def my_func():
        return await mock_func()

    with pytest.raises(ValueError, match="fail"):
        await my_func()

    assert mock_func.call_count == 3


def test_setup_structured_logging():
    logger = setup_structured_logging()
    assert logger.level <= 20  # INFO or lower
    # Verify at least one handler has a formatter attached
    assert any(h.formatter is not None for h in logger.handlers)
