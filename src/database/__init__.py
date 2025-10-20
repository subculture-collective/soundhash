"""Database package with repository pattern and session management.

This package provides database access through repositories with:
- Automatic retry on transient database errors
- Context managers for proper session lifecycle
- Idempotent job creation
- Standardized error handling and logging

Usage:
    # Option 1: Context manager (recommended for new code)
    from src.database.repositories import get_video_repo_session

    with get_video_repo_session() as repo:
        channel = repo.get_channel_by_id(channel_id)
        # Session automatically committed and closed

    # Option 2: Manual session management (for existing code)
    from src.database.repositories import get_video_repository

    repo = get_video_repository()
    channel = repo.get_channel_by_id(channel_id)
    # Note: Each method commits individually; session should be closed when done
    repo.session.close()
"""
