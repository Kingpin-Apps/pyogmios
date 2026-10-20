from unittest.mock import AsyncMock, patch

import pytest

from pyogmios.exceptions import RequestError
from pyogmios.models.server_health_model import ServerHealth
from pyogmios.server_health import get_server_health


@pytest.mark.asyncio
async def test_get_server_health(fake_server_health, mock_server_health_options):
    # Arrange
    mock_get = AsyncMock()
    mock_get.__aenter__.return_value.status = 200
    mock_get.__aenter__.return_value.json.return_value = fake_server_health
    with patch("aiohttp.ClientSession.get", return_value=mock_get):
        # Act
        server_health = await get_server_health(mock_server_health_options)

        # Assert
        assert server_health == ServerHealth.model_validate(fake_server_health)
        assert isinstance(server_health, ServerHealth)
        assert server_health.connection_status == "connected"


@pytest.mark.asyncio
async def test_get_server_health_error(mock_server_health_options):
    # Arrange
    status_code = 500
    mock_get = AsyncMock()
    mock_get.__aenter__.return_value.status = status_code
    mock_get.__aenter__.return_value.json.return_value = {}
    with patch("aiohttp.ClientSession.get", return_value=mock_get):
        # Act & Assert
        with pytest.raises(RequestError) as exc_info:
            await get_server_health(mock_server_health_options)
        assert str(exc_info.value) == f"Request error: {status_code}"
