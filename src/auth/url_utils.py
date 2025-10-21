"""
URL validation and sanitization utilities for authentication endpoints.
"""

from urllib.parse import urlparse, urlunparse


def sanitize_callback_url(base_url: str) -> str:
    """
    Sanitize and validate a callback base URL.

    This function ensures that the base URL is properly formatted and normalized
    to prevent URL injection vulnerabilities.

    Args:
        base_url: The base URL to sanitize

    Returns:
        The sanitized URL with scheme, netloc, and normalized path

    Raises:
        ValueError: If the URL is invalid or missing required components
    """
    if not base_url or not isinstance(base_url, str):
        raise ValueError("Base URL must be a non-empty string")

    # Strip whitespace
    base_url = base_url.strip()

    # Parse the URL
    parsed = urlparse(base_url)

    # Validate scheme
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Only http and https are allowed")

    # Validate netloc (hostname:port)
    if not parsed.netloc:
        raise ValueError("URL must contain a valid hostname")

    # Ensure no query parameters or fragments in base URL
    if parsed.query or parsed.fragment:
        raise ValueError("Base URL should not contain query parameters or fragments")

    # Normalize path - remove trailing slash for consistency
    path = parsed.path.rstrip("/")

    # Reconstruct the URL with only scheme, netloc, and normalized path
    sanitized = urlunparse(
        (parsed.scheme, parsed.netloc, path, "", "", "")  # params  # query  # fragment
    )

    return sanitized


def build_callback_url(base_url: str, path: str) -> str:
    """
    Build a callback URL by combining a sanitized base URL with a path.

    Args:
        base_url: The base URL to sanitize
        path: The path to append (should start with /)

    Returns:
        The complete callback URL

    Raises:
        ValueError: If the URL is invalid
    """
    if not path.startswith("/"):
        raise ValueError("Path must start with /")

    sanitized_base = sanitize_callback_url(base_url)
    return f"{sanitized_base}{path}"
