import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

try:
    from unittest.mock import AsyncMock
except ImportError:

    class AsyncMock(MagicMock):
        async def __call__(self, *args, **kwargs):
            return super(AsyncMock, self).__call__(*args, **kwargs)


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

    try:
        try:
            from pythonjsonlogger.json import JsonFormatter
        except ImportError:
            from pythonjsonlogger import jsonlogger

            JsonFormatter = jsonlogger.JsonFormatter
        has_json = True
    except ImportError:
        has_json = False

    if has_json:
        # Check if any handler has a formatter that looks like a JSON formatter
        # Newer versions might have different class names or structures
        assert any("Json" in type(h.formatter).__name__ for h in logger.handlers)
    else:
        assert any(
            isinstance(h.formatter, __import__("logging").Formatter) for h in logger.handlers
        )
