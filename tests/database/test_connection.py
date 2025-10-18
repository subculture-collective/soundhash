"""Tests for database connection."""

from unittest.mock import MagicMock, patch

from src.database.connection import DatabaseManager


class TestDatabaseManager:
    """Test suite for DatabaseManager class."""

    def test_init(self):
        """Test DatabaseManager initialization."""
        manager = DatabaseManager()

        assert manager.engine is None
        assert manager.Session is None

    def test_close_without_init(self):
        """Test closing without initialization doesn't error."""
        manager = DatabaseManager()

        # Should not raise an error
        manager.close()

    @patch("src.database.connection.create_engine")
    @patch("src.database.connection.sessionmaker")
    @patch("src.database.connection.Base")
    def test_initialize_mocked(self, mock_base, mock_sessionmaker, mock_create_engine):
        """Test initialization with mocked dependencies."""
        manager = DatabaseManager()

        # Mock the engine and session
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session_class = MagicMock()
        mock_sessionmaker.return_value = mock_session_class

        with patch("src.database.connection.Config") as mock_config:
            mock_config.get_database_url.return_value = "postgresql://user:pass@localhost/db"

            manager.initialize()

            assert manager.engine == mock_engine
            assert manager.Session == mock_session_class
            mock_base.metadata.create_all.assert_called_once_with(mock_engine)

    @patch("src.database.connection.create_engine")
    @patch("src.database.connection.sessionmaker")
    def test_get_session_initializes_if_needed(self, mock_sessionmaker, mock_create_engine):
        """Test that get_session initializes if not already initialized."""
        manager = DatabaseManager()

        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session_instance = MagicMock()
        mock_session_class = MagicMock(return_value=mock_session_instance)
        mock_sessionmaker.return_value = mock_session_class

        with patch("src.database.connection.Config") as mock_config:
            mock_config.get_database_url.return_value = "postgresql://user:pass@localhost/db"

            session = manager.get_session()

            assert session == mock_session_instance
            assert manager.Session is not None
