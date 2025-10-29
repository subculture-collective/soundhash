"""Tests for signature verification."""

import time

from src.security.signature_verification import SignatureVerifier


class TestSignatureVerifier:
    """Test signature verifier functionality."""

    def test_signature_verifier_init(self):
        """Test signature verifier initialization."""
        verifier = SignatureVerifier()
        assert verifier is not None

    def test_generate_signature(self):
        """Test signature generation."""
        verifier = SignatureVerifier(secret_key="test_secret_key")

        timestamp = str(int(time.time()))
        signature = verifier.generate_signature(
            method="GET",
            path="/api/v1/videos",
            body="",
            timestamp=timestamp,
            api_key="test_api_key",
        )

        assert signature is not None
        assert len(signature) > 0
        assert isinstance(signature, str)

    def test_verify_valid_signature(self):
        """Test verifying valid signature."""
        verifier = SignatureVerifier(secret_key="test_secret_key")

        timestamp = str(int(time.time()))
        method = "GET"
        path = "/api/v1/videos"
        body = ""
        api_key = "test_api_key"

        # Generate signature
        signature = verifier.generate_signature(method, path, body, timestamp, api_key)

        # Verify signature
        is_valid, error = verifier.verify_signature(
            method, path, body, timestamp, api_key, signature
        )

        assert is_valid is True
        assert error is None

    def test_verify_invalid_signature(self):
        """Test verifying invalid signature."""
        verifier = SignatureVerifier(secret_key="test_secret_key")

        timestamp = str(int(time.time()))
        is_valid, error = verifier.verify_signature(
            method="GET",
            path="/api/v1/videos",
            body="",
            timestamp=timestamp,
            api_key="test_api_key",
            provided_signature="invalid_signature",
        )

        assert is_valid is False
        assert error is not None
        assert "Invalid signature" in error

    def test_verify_old_timestamp(self):
        """Test verifying signature with old timestamp."""
        verifier = SignatureVerifier(secret_key="test_secret_key")

        # Use timestamp from 10 minutes ago
        old_timestamp = str(int(time.time()) - 600)

        # Generate signature with old timestamp
        signature = verifier.generate_signature(
            method="GET",
            path="/api/v1/videos",
            body="",
            timestamp=old_timestamp,
            api_key="test_api_key",
        )

        # Verify should fail due to old timestamp
        is_valid, error = verifier.verify_signature(
            method="GET",
            path="/api/v1/videos",
            body="",
            timestamp=old_timestamp,
            api_key="test_api_key",
            provided_signature=signature,
        )

        assert is_valid is False
        assert "Timestamp" in error

    def test_verify_future_timestamp(self):
        """Test verifying signature with future timestamp."""
        verifier = SignatureVerifier(secret_key="test_secret_key")

        # Use timestamp from 10 minutes in future
        future_timestamp = str(int(time.time()) + 600)

        # Generate signature with future timestamp
        signature = verifier.generate_signature(
            method="GET",
            path="/api/v1/videos",
            body="",
            timestamp=future_timestamp,
            api_key="test_api_key",
        )

        # Verify should fail due to future timestamp
        is_valid, error = verifier.verify_signature(
            method="GET",
            path="/api/v1/videos",
            body="",
            timestamp=future_timestamp,
            api_key="test_api_key",
            provided_signature=signature,
        )

        assert is_valid is False
        assert "Timestamp" in error

    def test_signature_different_methods(self):
        """Test that signature changes with different methods."""
        verifier = SignatureVerifier(secret_key="test_secret_key")

        timestamp = str(int(time.time()))
        path = "/api/v1/videos"
        body = ""
        api_key = "test_api_key"

        sig_get = verifier.generate_signature("GET", path, body, timestamp, api_key)
        sig_post = verifier.generate_signature("POST", path, body, timestamp, api_key)

        assert sig_get != sig_post

    def test_signature_different_paths(self):
        """Test that signature changes with different paths."""
        verifier = SignatureVerifier(secret_key="test_secret_key")

        timestamp = str(int(time.time()))
        method = "GET"
        body = ""
        api_key = "test_api_key"

        sig1 = verifier.generate_signature(method, "/api/v1/videos", body, timestamp, api_key)
        sig2 = verifier.generate_signature(method, "/api/v1/users", body, timestamp, api_key)

        assert sig1 != sig2

    def test_signature_different_bodies(self):
        """Test that signature changes with different bodies."""
        verifier = SignatureVerifier(secret_key="test_secret_key")

        timestamp = str(int(time.time()))
        method = "POST"
        path = "/api/v1/videos"
        api_key = "test_api_key"

        sig1 = verifier.generate_signature(method, path, '{"title": "Video 1"}', timestamp, api_key)
        sig2 = verifier.generate_signature(method, path, '{"title": "Video 2"}', timestamp, api_key)

        assert sig1 != sig2

    def test_signature_different_timestamps(self):
        """Test that signature changes with different timestamps."""
        verifier = SignatureVerifier(secret_key="test_secret_key")

        method = "GET"
        path = "/api/v1/videos"
        body = ""
        api_key = "test_api_key"

        timestamp1 = str(int(time.time()))
        time.sleep(1)
        timestamp2 = str(int(time.time()))

        sig1 = verifier.generate_signature(method, path, body, timestamp1, api_key)
        sig2 = verifier.generate_signature(method, path, body, timestamp2, api_key)

        assert sig1 != sig2

    def test_signature_different_api_keys(self):
        """Test that signature changes with different API keys."""
        verifier = SignatureVerifier(secret_key="test_secret_key")

        timestamp = str(int(time.time()))
        method = "GET"
        path = "/api/v1/videos"
        body = ""

        sig1 = verifier.generate_signature(method, path, body, timestamp, "api_key_1")
        sig2 = verifier.generate_signature(method, path, body, timestamp, "api_key_2")

        assert sig1 != sig2

    def test_extract_signature_headers(self):
        """Test extracting signature headers."""
        verifier = SignatureVerifier()

        headers = {
            "X-Timestamp": "1234567890",
            "X-Signature": "abc123def456",
            "X-API-Key": "test_api_key",
        }

        result = verifier.extract_signature_headers(headers)

        assert result["timestamp"] == "1234567890"
        assert result["signature"] == "abc123def456"
        assert result["api_key"] == "test_api_key"

    def test_extract_signature_headers_incomplete(self):
        """Test extracting incomplete signature headers."""
        verifier = SignatureVerifier()

        # Missing signature header
        headers = {
            "X-Timestamp": "1234567890",
            "X-API-Key": "test_api_key",
        }

        result = verifier.extract_signature_headers(headers)

        assert result == {}

    def test_invalid_timestamp_format(self):
        """Test handling invalid timestamp format."""
        verifier = SignatureVerifier(secret_key="test_secret_key")

        is_valid, error = verifier.verify_signature(
            method="GET",
            path="/api/v1/videos",
            body="",
            timestamp="invalid_timestamp",
            api_key="test_api_key",
            provided_signature="signature",
        )

        assert is_valid is False
        assert "timestamp" in error.lower()
