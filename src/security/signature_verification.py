"""Request signature verification for API security."""

import hashlib
import hmac
import logging
import time
from typing import Optional

from config.settings import Config

logger = logging.getLogger(__name__)


class SignatureVerifier:
    """Verify request signatures for API security."""

    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize signature verifier.
        
        Args:
            secret_key: Secret key for HMAC. Uses API_SECRET_KEY if not provided.
        """
        self.secret_key = (secret_key or Config.API_SECRET_KEY).encode("utf-8")
        self.max_timestamp_delta = Config.SIGNATURE_MAX_TIMESTAMP_DELTA  # seconds

    def generate_signature(
        self,
        method: str,
        path: str,
        body: str,
        timestamp: str,
        api_key: str,
    ) -> str:
        """
        Generate HMAC-SHA256 signature for request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            body: Request body (empty string for GET)
            timestamp: Unix timestamp as string
            api_key: API key
        
        Returns:
            Hex digest of HMAC signature
        """
        # Construct message to sign
        message = f"{method}|{path}|{body}|{timestamp}|{api_key}".encode("utf-8")
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()
        
        return signature

    def verify_signature(
        self,
        method: str,
        path: str,
        body: str,
        timestamp: str,
        api_key: str,
        provided_signature: str,
    ) -> tuple[bool, Optional[str]]:
        """
        Verify request signature.
        
        Args:
            method: HTTP method
            path: Request path
            body: Request body
            timestamp: Timestamp from request header
            api_key: API key from request header
            provided_signature: Signature from request header
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Verify timestamp is recent
            current_time = int(time.time())
            request_time = int(timestamp)
            
            time_delta = abs(current_time - request_time)
            if time_delta > self.max_timestamp_delta:
                return False, f"Timestamp too old or too far in future (delta: {time_delta}s)"
            
            # Generate expected signature
            expected_signature = self.generate_signature(
                method, path, body, timestamp, api_key
            )
            
            # Compare signatures using constant-time comparison
            if not hmac.compare_digest(expected_signature, provided_signature):
                return False, "Invalid signature"
            
            return True, None
            
        except ValueError as e:
            return False, f"Invalid timestamp format: {e}"
        except Exception as e:
            logger.error(f"Signature verification error: {e}", exc_info=True)
            return False, "Signature verification failed"

    def extract_signature_headers(self, headers: dict) -> dict:
        """
        Extract signature-related headers from request.
        
        Args:
            headers: Request headers dictionary
        
        Returns:
            Dictionary with signature components or empty dict if incomplete
        """
        timestamp = headers.get("X-Timestamp")
        signature = headers.get("X-Signature")
        api_key = headers.get("X-API-Key")
        
        if not all([timestamp, signature, api_key]):
            return {}
        
        return {
            "timestamp": timestamp,
            "signature": signature,
            "api_key": api_key,
        }
