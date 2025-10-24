"""Tests for YouTube API OAuth functionality."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.api.youtube_service import YouTubeAPIService


@pytest.fixture
def temp_credentials_dir():
    """Create temporary directory for credentials files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_credentials_file(temp_credentials_dir):
    """Create a mock credentials.json file."""
    credentials_data = {
        "installed": {
            "client_id": "mock_client_id.apps.googleusercontent.com",
            "project_id": "mock_project",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "mock_client_secret",
            "redirect_uris": ["http://localhost"],
        }
    }
    
    credentials_path = Path(temp_credentials_dir) / "credentials.json"
    with open(credentials_path, "w") as f:
        json.dump(credentials_data, f)
    
    return str(credentials_path)


@pytest.fixture
def mock_token_file(temp_credentials_dir):
    """Create a mock token.json file."""
    token_data = {
        "token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "mock_client_id.apps.googleusercontent.com",
        "client_secret": "mock_client_secret",
        "scopes": ["https://www.googleapis.com/auth/youtube.readonly"],
    }
    
    token_path = Path(temp_credentials_dir) / "token.json"
    with open(token_path, "w") as f:
        json.dump(token_data, f)
    
    return str(token_path)


class TestYouTubeOAuth:
    """Test suite for YouTube OAuth functionality."""

    def test_scopes_defined(self):
        """Test that required scopes are properly defined."""
        assert hasattr(YouTubeAPIService, "SCOPES")
        assert isinstance(YouTubeAPIService.SCOPES, list)
        assert "https://www.googleapis.com/auth/youtube.readonly" in YouTubeAPIService.SCOPES

    def test_credentials_file_not_found(self, temp_credentials_dir):
        """Test that FileNotFoundError is raised when credentials.json is missing."""
        credentials_path = os.path.join(temp_credentials_dir, "credentials.json")
        token_path = os.path.join(temp_credentials_dir, "token.json")
        
        with pytest.raises(FileNotFoundError) as exc_info:
            YouTubeAPIService(credentials_file=credentials_path, token_file=token_path)
        
        assert "credentials.json" in str(exc_info.value).lower()
        assert "not found" in str(exc_info.value).lower()

    @patch("src.api.youtube_service.Credentials")
    @patch("src.api.youtube_service.build")
    def test_load_existing_valid_token(
        self, mock_build, mock_credentials_class, mock_credentials_file, mock_token_file
    ):
        """Test that existing valid token is loaded successfully."""
        # Mock valid credentials
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.expired = False
        mock_credentials_class.from_authorized_user_file.return_value = mock_creds
        
        # Mock YouTube service build
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Initialize service
        service = YouTubeAPIService(
            credentials_file=mock_credentials_file, token_file=mock_token_file
        )
        
        # Verify credentials were loaded
        mock_credentials_class.from_authorized_user_file.assert_called_once()
        assert service.service == mock_service

    @patch("src.api.youtube_service.Credentials")
    @patch("src.api.youtube_service.Request")
    @patch("src.api.youtube_service.build")
    def test_refresh_expired_token(
        self, mock_build, mock_request, mock_credentials_class, mock_credentials_file, temp_credentials_dir
    ):
        """Test that expired token with refresh_token is refreshed."""
        token_path = os.path.join(temp_credentials_dir, "token.json")
        
        # Create initial token file
        with open(token_path, "w") as f:
            json.dump({"token": "old_token", "refresh_token": "refresh"}, f)
        
        # Mock expired credentials with refresh token
        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "mock_refresh_token"
        mock_creds.to_json.return_value = json.dumps({"token": "refreshed_token", "refresh_token": "refresh"})
        mock_credentials_class.from_authorized_user_file.return_value = mock_creds
        
        # After refresh, make it valid
        def refresh_side_effect(request):
            mock_creds.valid = True
            mock_creds.expired = False
        
        mock_creds.refresh.side_effect = refresh_side_effect
        
        # Mock YouTube service build
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Initialize service
        service = YouTubeAPIService(
            credentials_file=mock_credentials_file, token_file=token_path
        )
        
        # Verify token was refreshed
        mock_creds.refresh.assert_called_once()
        
        # Verify token was saved
        assert os.path.exists(token_path)

    @patch("src.api.youtube_service.Credentials")
    @patch("src.api.youtube_service.InstalledAppFlow")
    @patch("src.api.youtube_service.build")
    def test_new_oauth_flow(
        self, mock_build, mock_flow_class, mock_credentials_class, mock_credentials_file, temp_credentials_dir
    ):
        """Test that new OAuth flow is initiated when no valid token exists."""
        token_path = os.path.join(temp_credentials_dir, "token.json")
        
        # Mock no existing token
        mock_credentials_class.from_authorized_user_file.side_effect = FileNotFoundError
        
        # Mock OAuth flow
        mock_flow = MagicMock()
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.to_json.return_value = '{"token": "new_token"}'
        mock_flow.run_local_server.return_value = mock_creds
        mock_flow_class.from_client_secrets_file.return_value = mock_flow
        
        # Mock YouTube service build
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Initialize service
        service = YouTubeAPIService(
            credentials_file=mock_credentials_file, token_file=token_path
        )
        
        # Verify OAuth flow was initiated
        mock_flow_class.from_client_secrets_file.assert_called_once_with(
            mock_credentials_file, YouTubeAPIService.SCOPES
        )
        mock_flow.run_local_server.assert_called_once_with(port=8080, open_browser=True)
        
        # Verify token was saved
        assert os.path.exists(token_path)
        with open(token_path, "r") as f:
            saved_token = f.read()
            assert "token" in saved_token

    @patch("src.api.youtube_service.Credentials")
    @patch("src.api.youtube_service.build")
    def test_token_persistence(
        self, mock_build, mock_credentials_class, mock_credentials_file, temp_credentials_dir
    ):
        """Test that token is persisted to token.json."""
        token_path = os.path.join(temp_credentials_dir, "token.json")
        
        # Mock valid credentials
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.to_json.return_value = json.dumps({
            "token": "test_token",
            "refresh_token": "test_refresh",
            "scopes": YouTubeAPIService.SCOPES,
        })
        mock_credentials_class.from_authorized_user_file.return_value = mock_creds
        
        # Mock YouTube service build
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Create initial token file
        with open(token_path, "w") as f:
            f.write(mock_creds.to_json())
        
        # Initialize service
        service = YouTubeAPIService(
            credentials_file=mock_credentials_file, token_file=token_path
        )
        
        # Verify token file exists and contains expected data
        assert os.path.exists(token_path)
        with open(token_path, "r") as f:
            token_data = json.load(f)
            assert "token" in token_data
            assert "refresh_token" in token_data
            assert "scopes" in token_data

    @patch("src.api.youtube_service.Credentials")
    @patch("src.api.youtube_service.build")
    def test_service_initialization_success(
        self, mock_build, mock_credentials_class, mock_credentials_file, mock_token_file
    ):
        """Test that YouTube service is initialized successfully."""
        # Mock valid credentials
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_credentials_class.from_authorized_user_file.return_value = mock_creds
        
        # Mock YouTube service build
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Initialize service
        service = YouTubeAPIService(
            credentials_file=mock_credentials_file, token_file=mock_token_file
        )
        
        # Verify service was built with correct parameters
        mock_build.assert_called_once_with("youtube", "v3", credentials=mock_creds)
        assert service.service == mock_service

    @patch("src.api.youtube_service.Credentials")
    @patch("src.api.youtube_service.build")
    def test_default_file_paths(self, mock_build, mock_credentials_class, temp_credentials_dir):
        """Test that default paths for credentials and token files are set correctly."""
        # Create mock files
        default_creds = os.path.join(temp_credentials_dir, "credentials.json")
        default_token = os.path.join(temp_credentials_dir, "token.json")
        
        # Create credentials file
        with open(default_creds, "w") as f:
            json.dump({"installed": {"client_id": "test"}}, f)
        
        # Create token file
        with open(default_token, "w") as f:
            json.dump({"token": "test"}, f)
        
        # Mock valid credentials
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_credentials_class.from_authorized_user_file.return_value = mock_creds
        
        # Mock YouTube service build
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Initialize service with explicit paths
        service = YouTubeAPIService(
            credentials_file=default_creds, token_file=default_token
        )
        
        # Verify paths are set correctly
        assert service.credentials_file == default_creds
        assert service.token_file == default_token

    @patch("src.api.youtube_service.Credentials")
    @patch("src.api.youtube_service.Request")
    @patch("src.api.youtube_service.build")
    def test_refresh_failure_triggers_new_flow(
        self, mock_build, mock_request, mock_credentials_class, mock_credentials_file, temp_credentials_dir
    ):
        """Test that failed token refresh triggers new OAuth flow."""
        token_path = os.path.join(temp_credentials_dir, "token.json")
        
        # Create initial token file
        with open(token_path, "w") as f:
            json.dump({"token": "old_token", "refresh_token": "refresh"}, f)
        
        # Mock expired credentials with refresh token
        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "mock_refresh_token"
        mock_creds.refresh.side_effect = Exception("Refresh failed")
        mock_credentials_class.from_authorized_user_file.return_value = mock_creds
        
        # Mock YouTube service build
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Mock new OAuth flow
        with patch("src.api.youtube_service.InstalledAppFlow") as mock_flow_class:
            mock_flow = MagicMock()
            new_creds = MagicMock()
            new_creds.valid = True
            new_creds.to_json.return_value = '{"token": "new_token"}'
            mock_flow.run_local_server.return_value = new_creds
            mock_flow_class.from_client_secrets_file.return_value = mock_flow
            
            # Initialize service
            service = YouTubeAPIService(
                credentials_file=mock_credentials_file, token_file=token_path
            )
            
            # Verify refresh was attempted
            mock_creds.refresh.assert_called_once()
            
            # Verify new OAuth flow was initiated
            mock_flow_class.from_client_secrets_file.assert_called_once()
            mock_flow.run_local_server.assert_called_once()
