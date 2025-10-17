"""
YouTube Data API v3 Service
Handles authentication and API calls for YouTube channel and video data.
"""

import logging
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class YouTubeAPIService:
    """YouTube Data API v3 service with OAuth authentication"""

    # OAuth 2.0 scopes for YouTube Data API
    SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

    def __init__(self, credentials_file: str = None, token_file: str = None):
        """
        Initialize YouTube API service

        Args:
            credentials_file: Path to OAuth2 client credentials JSON
            token_file: Path to store/load OAuth2 tokens
        """
        self.logger = logging.getLogger(__name__)
        self.service = None

        # Default paths for credentials and tokens
        self.credentials_file = credentials_file or os.path.join(os.getcwd(), "credentials.json")
        self.token_file = token_file or os.path.join(os.getcwd(), "token.json")

        # Initialize the service
        self._authenticate()

    def _authenticate(self):
        """Handle OAuth2 authentication flow"""
        creds = None

        # Load existing token if available
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
                self.logger.info("Loaded existing OAuth2 token")
            except Exception as e:
                self.logger.warning(f"Failed to load existing token: {e}")

        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self.logger.info("Refreshed expired OAuth2 token")
                except Exception as e:
                    self.logger.warning(f"Failed to refresh token: {e}")
                    creds = None

            if not creds:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"OAuth2 credentials file not found: {self.credentials_file}\\n"
                        f"Please download from Google Cloud Console and place at: {self.credentials_file}"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.SCOPES)
                # Use fixed port to avoid redirect URI mismatch
                creds = flow.run_local_server(port=8080, open_browser=True)
                self.logger.info("Completed OAuth2 authentication flow")

            # Save the credentials for the next run
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())
                self.logger.info(f"Saved OAuth2 token to: {self.token_file}")

        # Build the YouTube service
        try:
            self.service = build("youtube", "v3", credentials=creds)
            self.logger.info("YouTube API service initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to build YouTube service: {e}")
            raise

    def get_channel_info(self, channel_id: str) -> dict | None:
        """
        Get basic channel information

        Args:
            channel_id: YouTube channel ID

        Returns:
            Dictionary with channel information or None if error
        """
        try:
            request = self.service.channels().list(part="snippet,statistics", id=channel_id)
            response = request.execute()

            if "items" in response and response["items"]:
                channel = response["items"][0]
                return {
                    "id": channel["id"],
                    "title": channel["snippet"]["title"],
                    "description": channel["snippet"]["description"],
                    "thumbnail": channel["snippet"]["thumbnails"].get("default", {}).get("url"),
                    "subscriber_count": channel["statistics"].get("subscriberCount"),
                    "video_count": channel["statistics"].get("videoCount"),
                    "view_count": channel["statistics"].get("viewCount"),
                }
            return None

        except HttpError as e:
            self.logger.error(f"HTTP error getting channel info for {channel_id}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting channel info for {channel_id}: {e}")
            return None

    def get_channel_videos(self, channel_id: str, max_results: int = None) -> list[dict]:
        """
        Get list of videos from a channel

        Args:
            channel_id: YouTube channel ID
            max_results: Maximum number of videos to return (None for unlimited)

        Returns:
            List of video information dictionaries
        """
        try:
            videos = []

            # Handle unlimited case
            if max_results is None:
                max_results = float("inf")
                self.logger.info(f"Fetching ALL videos from channel {channel_id}")
            else:
                self.logger.info(f"Fetching up to {max_results} videos from channel {channel_id}")

            # First, get the channel's uploads playlist ID
            channel_request = self.service.channels().list(part="contentDetails", id=channel_id)
            channel_response = channel_request.execute()

            if not channel_response["items"]:
                self.logger.warning(f"Channel not found: {channel_id}")
                return []

            uploads_playlist_id = channel_response["items"][0]["contentDetails"][
                "relatedPlaylists"
            ]["uploads"]

            # Get videos from the uploads playlist
            next_page_token = None
            retrieved_count = 0

            while retrieved_count < max_results:
                # Calculate how many to fetch this round (max 50 per API call)
                batch_size = (
                    min(50, max_results - retrieved_count) if max_results != float("inf") else 50
                )

                request = self.service.playlistItems().list(
                    part="snippet",
                    playlistId=uploads_playlist_id,
                    maxResults=batch_size,
                    pageToken=next_page_token,
                )
                response = request.execute()

                # Extract video IDs for detailed info
                video_ids = [item["snippet"]["resourceId"]["videoId"] for item in response["items"]]

                # Get detailed video information
                video_details = self.get_video_details(video_ids)
                videos.extend(video_details)
                retrieved_count += len(video_details)

                # Check if there are more pages
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

            self.logger.info(f"Retrieved {len(videos)} videos for channel {channel_id}")
            return videos

        except HttpError as e:
            self.logger.error(f"HTTP error getting videos for channel {channel_id}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error getting videos for channel {channel_id}: {e}")
            return []

    def get_video_details(self, video_ids: list[str]) -> list[dict]:
        """
        Get detailed information for a list of video IDs

        Args:
            video_ids: List of YouTube video IDs

        Returns:
            List of video information dictionaries
        """
        if not video_ids:
            return []

        try:
            # YouTube API allows up to 50 video IDs per request
            videos = []

            for i in range(0, len(video_ids), 50):
                batch_ids = video_ids[i : i + 50]

                request = self.service.videos().list(
                    part="snippet,statistics,contentDetails", id=",".join(batch_ids)
                )
                response = request.execute()

                for video in response["items"]:
                    # Parse duration from ISO 8601 format (PT4M13S) to seconds
                    duration_str = video["contentDetails"]["duration"]
                    duration_seconds = self._parse_duration(duration_str)

                    video_info = {
                        "id": video["id"],
                        "title": video["snippet"]["title"],
                        "description": video["snippet"]["description"],
                        "duration": duration_seconds,
                        "upload_date": video["snippet"]["publishedAt"][:10].replace(
                            "-", ""
                        ),  # YYYYMMDD format
                        "view_count": int(video["statistics"].get("viewCount", 0)),
                        "like_count": int(video["statistics"].get("likeCount", 0)),
                        "channel": video["snippet"]["channelTitle"],
                        "channel_id": video["snippet"]["channelId"],
                        "thumbnail": video["snippet"]["thumbnails"].get("default", {}).get("url"),
                        "webpage_url": f"https://www.youtube.com/watch?v={video['id']}",
                    }
                    videos.append(video_info)

            return videos

        except HttpError as e:
            self.logger.error(f"HTTP error getting video details: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error getting video details: {e}")
            return []

    def _parse_duration(self, duration_str: str) -> int | None:
        """
        Parse ISO 8601 duration (PT4M13S) to seconds

        Args:
            duration_str: ISO 8601 duration string

        Returns:
            Duration in seconds or None if parsing fails
        """
        try:
            import re

            # Remove PT prefix
            duration_str = duration_str[2:] if duration_str.startswith("PT") else duration_str

            # Parse hours, minutes, seconds
            hours = 0
            minutes = 0
            seconds = 0

            # Extract hours
            h_match = re.search(r"(\\d+)H", duration_str)
            if h_match:
                hours = int(h_match.group(1))

            # Extract minutes
            m_match = re.search(r"(\\d+)M", duration_str)
            if m_match:
                minutes = int(m_match.group(1))

            # Extract seconds
            s_match = re.search(r"(\\d+)S", duration_str)
            if s_match:
                seconds = int(s_match.group(1))

            return hours * 3600 + minutes * 60 + seconds

        except Exception as e:
            self.logger.warning(f"Failed to parse duration '{duration_str}': {e}")
            return None

    def test_connection(self) -> bool:
        """
        Test if the YouTube API connection is working

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Simple API call to test connectivity
            request = self.service.channels().list(part="snippet", mine=True)
            _ = request.execute()
            self.logger.info("YouTube API connection test successful")
            return True

        except HttpError as e:
            self.logger.error(f"YouTube API connection test failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"YouTube API connection test error: {e}")
            return False
