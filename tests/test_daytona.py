from unittest.mock import MagicMock, patch

import pytest

from ai_dev_os.utils.daytona import DaytonaClient


@pytest.mark.asyncio
async def test_daytona_client_mock_mode():
    client = DaytonaClient(api_key=None)
    ws_id = await client.create_workspace("test")
    assert "mock-workspace-test" in ws_id

    res = await client.execute_command(ws_id, "ls")
    assert res["exit_code"] == 0

    forward_url = await client.setup_port_forward(ws_id, 8080)
    assert "localhost:8080" in forward_url


@pytest.mark.asyncio
async def test_daytona_client_real_interaction():
    client = DaytonaClient(api_key="fake-key")
    with patch("httpx.AsyncClient.post") as mock_post:
        # Mock simple response
        ws_id = await client.create_workspace("real-unit-test")
        assert "daytona-" in ws_id
