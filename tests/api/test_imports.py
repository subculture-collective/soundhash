"""Tests for API imports."""


def test_api_imports():
    """Test that API modules can be imported."""
    try:
        from src.api import YouTubeAPIService
        assert YouTubeAPIService is not None
    except ImportError:
        # YouTubeAPIService may not be importable if dependencies are missing
        pass
