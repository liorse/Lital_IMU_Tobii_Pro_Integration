"""Shared test fixtures"""
import pytest
from unittest.mock import Mock, MagicMock, patch

@pytest.fixture
def mock_app():
    """Mock ScopeFoundry app"""
    app = Mock()
    app.settings = {}
    app.log = Mock()
    return app

@pytest.fixture
def mock_serial():
    """Mock serial port"""
    with patch('serial.Serial') as mock:
        mock_instance = MagicMock()
        mock_instance.is_open = True
        mock_instance.write.return_value = 2
        mock.return_value = mock_instance
        yield mock_instance
