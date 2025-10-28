"""Tests for WebSocket connection manager."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.websocket import ConnectionManager


@pytest.fixture
def connection_manager():
    """Create a fresh connection manager for each test."""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


class TestConnectionManager:
    """Test suite for ConnectionManager."""

    @pytest.mark.asyncio
    async def test_connect(self, connection_manager, mock_websocket):
        """Test connecting a WebSocket client."""
        client_id = "test-client-1"
        
        await connection_manager.connect(mock_websocket, client_id)
        
        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()
        
        # Verify client was registered
        assert client_id in connection_manager.active_connections
        assert connection_manager.active_connections[client_id] == mock_websocket
        assert client_id in connection_manager.user_streams
        assert client_id in connection_manager.connection_times

    def test_disconnect(self, connection_manager, mock_websocket):
        """Test disconnecting a client."""
        client_id = "test-client-1"
        
        # Manually add connection
        connection_manager.active_connections[client_id] = mock_websocket
        connection_manager.user_streams[client_id] = []
        connection_manager.connection_times[client_id] = 0.0
        
        # Disconnect
        connection_manager.disconnect(client_id)
        
        # Verify cleanup
        assert client_id not in connection_manager.active_connections
        assert client_id not in connection_manager.user_streams
        assert client_id not in connection_manager.connection_times

    @pytest.mark.asyncio
    async def test_send_match(self, connection_manager, mock_websocket):
        """Test sending match data to client."""
        client_id = "test-client-1"
        connection_manager.active_connections[client_id] = mock_websocket
        
        match_data = {
            "matches": [{"video_id": "123", "title": "Test Video"}],
            "timestamp": 1234567890
        }
        
        await connection_manager.send_match(client_id, match_data)
        
        # Verify send_json was called with correct data
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "match"
        assert call_args["data"] == match_data

    @pytest.mark.asyncio
    async def test_send_status(self, connection_manager, mock_websocket):
        """Test sending status update to client."""
        client_id = "test-client-1"
        connection_manager.active_connections[client_id] = mock_websocket
        
        status = "Processing audio"
        
        await connection_manager.send_status(client_id, status)
        
        # Verify send_json was called
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "status"
        assert call_args["message"] == status

    @pytest.mark.asyncio
    async def test_send_error(self, connection_manager, mock_websocket):
        """Test sending error message to client."""
        client_id = "test-client-1"
        connection_manager.active_connections[client_id] = mock_websocket
        
        error_msg = "Processing failed"
        
        await connection_manager.send_error(client_id, error_msg)
        
        # Verify send_json was called
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["message"] == error_msg

    @pytest.mark.asyncio
    async def test_send_to_disconnected_client(self, connection_manager):
        """Test sending to a client that doesn't exist."""
        client_id = "nonexistent-client"
        
        # Should not raise an exception
        await connection_manager.send_match(client_id, {})
        await connection_manager.send_status(client_id, "test")
        await connection_manager.send_error(client_id, "test")

    def test_get_active_connections(self, connection_manager, mock_websocket):
        """Test getting list of active connections."""
        # Add some connections
        connection_manager.active_connections["client-1"] = mock_websocket
        connection_manager.connection_times["client-1"] = 1000.0
        
        connection_manager.active_connections["client-2"] = mock_websocket
        connection_manager.connection_times["client-2"] = 2000.0
        
        # Get active connections
        connections = connection_manager.get_active_connections()
        
        assert len(connections) == 2
        assert any(c["client_id"] == "client-1" for c in connections)
        assert any(c["client_id"] == "client-2" for c in connections)
        
        # Verify each connection has required fields
        for conn in connections:
            assert "client_id" in conn
            assert "connected_at" in conn
            assert "duration_seconds" in conn

    @pytest.mark.asyncio
    async def test_send_json_error_disconnects_client(self, connection_manager, mock_websocket):
        """Test that send errors cause disconnection."""
        client_id = "test-client-1"
        connection_manager.active_connections[client_id] = mock_websocket
        connection_manager.user_streams[client_id] = []
        connection_manager.connection_times[client_id] = 0.0
        
        # Make send_json raise an exception
        mock_websocket.send_json.side_effect = Exception("Connection error")
        
        # Try to send a message
        await connection_manager.send_match(client_id, {})
        
        # Client should be disconnected
        assert client_id not in connection_manager.active_connections


def test_global_manager_instance():
    """Test that global manager instance exists."""
    from src.api.websocket import manager
    
    assert isinstance(manager, ConnectionManager)
    assert hasattr(manager, 'active_connections')
    assert hasattr(manager, 'user_streams')
