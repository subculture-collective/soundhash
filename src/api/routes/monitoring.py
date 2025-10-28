"""Live monitoring routes for WebSocket streams."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_current_user
from src.api.websocket import manager
from src.core.streaming_processor import cleanup_processor, processors
from src.database.models import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/live-streams")
async def get_live_streams(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get all active live streams.

    Requires authentication. Returns information about all active
    WebSocket connections and their processing status.
    """
    # Check if user is admin (for now, allow all authenticated users)
    # In production, would check current_user.is_admin or similar

    connections = manager.get_active_connections()

    # Enrich with processor information
    stream_info = []
    for conn in connections:
        client_id = conn["client_id"]
        processor = processors.get(client_id)

        info = {
            **conn,
            "has_processor": processor is not None,
        }

        if processor:
            info.update(processor.get_stats())

        stream_info.append(info)

    return {
        "total_streams": len(stream_info),
        "streams": stream_info
    }


@router.delete("/live-streams/{client_id}")
async def disconnect_stream(
    client_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Disconnect a live stream.

    Requires authentication. Forcefully disconnects a client
    and cleans up their resources.
    """
    # Check if user is admin (for now, allow all authenticated users)
    # In production, would check current_user.is_admin or similar

    if client_id in manager.active_connections:
        # Send disconnect message
        await manager.send_status(client_id, "Connection terminated by administrator")

        # Disconnect and cleanup
        manager.disconnect(client_id)
        cleanup_processor(client_id)

        return {"message": f"Disconnected stream {client_id}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stream {client_id} not found"
        )


@router.get("/live-streams/{client_id}")
async def get_stream_details(
    client_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get detailed information about a specific stream."""
    if client_id not in manager.active_connections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stream {client_id} not found"
        )

    # Get connection info
    connections = manager.get_active_connections()
    conn_info = next((c for c in connections if c["client_id"] == client_id), None)

    if not conn_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stream {client_id} not found"
        )

    # Get processor info
    processor = processors.get(client_id)

    result = {
        **conn_info,
        "has_processor": processor is not None,
    }

    if processor:
        result.update(processor.get_stats())

    return result
