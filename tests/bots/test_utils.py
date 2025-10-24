"""Tests for bot utility functions and decorators."""

from unittest.mock import Mock, patch

import pytest
from tweepy.errors import TooManyRequests, TwitterServerError

from src.bots.utils import twitter_retry


class TestTwitterRetryDecorator:
    """Test suite for twitter_retry decorator."""

    @patch("src.bots.utils.time.sleep")
    def test_retry_on_rate_limit(self, mock_sleep):
        """Test that decorator retries on TooManyRequests."""
        mock_response = Mock()
        mock_response.json.return_value = {}

        call_count = 0

        @twitter_retry(max_retries=3, initial_delay=5)
        def mock_api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TooManyRequests(mock_response, response_json={})
            return "success"

        result = mock_api_call()

        assert result == "success"
        assert call_count == 3
        assert mock_sleep.call_count == 2  # Two retries before success

    @patch("src.bots.utils.time.sleep")
    def test_retry_on_server_error(self, mock_sleep):
        """Test that decorator retries on TwitterServerError."""
        mock_response = Mock()
        mock_response.json.return_value = {}

        call_count = 0

        @twitter_retry(max_retries=3, initial_delay=5)
        def mock_api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TwitterServerError(mock_response, response_json={})
            return "success"

        result = mock_api_call()

        assert result == "success"
        assert call_count == 2
        assert mock_sleep.call_count == 1

    @patch("src.bots.utils.time.sleep")
    def test_exponential_backoff(self, mock_sleep):
        """Test that retry uses exponential backoff."""
        mock_response = Mock()
        mock_response.json.return_value = {}

        call_count = 0

        @twitter_retry(max_retries=4, initial_delay=2)
        def mock_api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                raise TwitterServerError(mock_response, response_json={})
            return "success"

        result = mock_api_call()

        assert result == "success"
        # Check exponential backoff: 2*(2^0)=2, 2*(2^1)=4, 2*(2^2)=8
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert sleep_calls == [2, 4, 8]

    @patch("src.bots.utils.time.sleep")
    def test_max_retries_exceeded_rate_limit(self, mock_sleep):
        """Test that decorator raises exception after max retries for rate limit."""
        mock_response = Mock()
        mock_response.json.return_value = {}

        @twitter_retry(max_retries=2, initial_delay=5)
        def mock_api_call():
            raise TooManyRequests(mock_response, response_json={})

        with pytest.raises(TooManyRequests):
            mock_api_call()

        assert mock_sleep.call_count == 1  # One retry before giving up

    @patch("src.bots.utils.time.sleep")
    def test_max_retries_exceeded_server_error(self, mock_sleep):
        """Test that decorator raises exception after max retries for server error."""
        mock_response = Mock()
        mock_response.json.return_value = {}

        @twitter_retry(max_retries=2, initial_delay=5)
        def mock_api_call():
            raise TwitterServerError(mock_response, response_json={})

        with pytest.raises(TwitterServerError):
            mock_api_call()

        assert mock_sleep.call_count == 1

    @patch("src.bots.utils.time.sleep")
    @patch("src.bots.utils.time.time")
    def test_rate_limit_with_reset_time(self, mock_time, mock_sleep):
        """Test that decorator uses reset_time from rate limit error when available."""
        mock_response = Mock()
        mock_response.json.return_value = {}

        # Current time is 100, reset time is 120, so wait time should be 21 seconds (120-100+1)
        mock_time.return_value = 100

        call_count = 0

        @twitter_retry(max_retries=2, initial_delay=5)
        def mock_api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                error = TooManyRequests(mock_response, response_json={})
                error.reset_time = 120
                raise error
            return "success"

        result = mock_api_call()

        assert result == "success"
        assert call_count == 2
        # Should use reset_time: max(120 - 100, 0) + 1 = 21
        mock_sleep.assert_called_once_with(21)

    def test_non_retryable_exception(self):
        """Test that non-retryable exceptions are propagated immediately."""
        @twitter_retry(max_retries=3)
        def mock_api_call():
            raise ValueError("Not a Twitter error")

        with pytest.raises(ValueError, match="Not a Twitter error"):
            mock_api_call()

    def test_successful_call_no_retry(self):
        """Test that successful calls don't trigger any retries."""
        call_count = 0

        @twitter_retry(max_retries=3)
        def mock_api_call():
            nonlocal call_count
            call_count += 1
            return "success"

        result = mock_api_call()

        assert result == "success"
        assert call_count == 1

    @patch("src.bots.utils.time.sleep")
    def test_decorator_preserves_function_metadata(self, mock_sleep):
        """Test that decorator preserves original function name and docstring."""
        @twitter_retry(max_retries=3)
        def my_function():
            """This is my function."""
            return "result"

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "This is my function."

    @patch("src.bots.utils.time.sleep")
    def test_mixed_error_types(self, mock_sleep):
        """Test retry behavior with mixed error types."""
        mock_response = Mock()
        mock_response.json.return_value = {}

        call_count = 0

        @twitter_retry(max_retries=4, initial_delay=2)
        def mock_api_call():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TooManyRequests(mock_response, response_json={})
            elif call_count == 2:
                raise TwitterServerError(mock_response, response_json={})
            elif call_count == 3:
                raise TooManyRequests(mock_response, response_json={})
            return "success"

        result = mock_api_call()

        assert result == "success"
        assert call_count == 4
        assert mock_sleep.call_count == 3
