#!/usr/bin/env python3
"""
Webhook Testing Tool for SoundHash API.

Test your webhook endpoints by sending sample events with proper signatures.

Usage:
    python scripts/test_webhook.py --url URL --event EVENT --secret SECRET
    
Examples:
    python scripts/test_webhook.py \
        --url https://myapp.com/webhooks/soundhash \
        --event video.processed \
        --secret my-webhook-secret
"""

import argparse
import hashlib
import hmac
import json
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any

try:
    import requests
except ImportError:
    print("❌ requests library required. Install with: pip install requests")
    sys.exit(1)


# Sample event payloads
SAMPLE_EVENTS = {
    "video.uploaded": {
        "id": 123,
        "title": "Test Video",
        "url": "https://youtube.com/watch?v=test123",
        "duration": 0,
        "status": "uploaded",
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    },
    "video.processing": {
        "id": 123,
        "title": "Test Video",
        "url": "https://youtube.com/watch?v=test123",
        "duration": 180,
        "status": "processing",
        "job_id": "job_abc123"
    },
    "video.processed": {
        "id": 123,
        "title": "Test Video",
        "url": "https://youtube.com/watch?v=test123",
        "duration": 180,
        "status": "processed",
        "fingerprints": [
            {
                "id": 456,
                "segment_index": 0,
                "start_time": 0,
                "end_time": 90
            },
            {
                "id": 457,
                "segment_index": 1,
                "start_time": 90,
                "end_time": 180
            }
        ],
        "processing_time": 45.2
    },
    "video.failed": {
        "id": 123,
        "title": "Test Video",
        "url": "https://youtube.com/watch?v=test123",
        "status": "failed",
        "error": "Failed to download video",
        "error_code": "DOWNLOAD_ERROR"
    },
    "match.found": {
        "query_id": "q_test123",
        "matches": [
            {
                "video_id": 123,
                "title": "Matched Video",
                "confidence": 0.95,
                "start_time": 45,
                "end_time": 60,
                "similarity_score": 0.94
            },
            {
                "video_id": 124,
                "title": "Another Match",
                "confidence": 0.87,
                "start_time": 10,
                "end_time": 25,
                "similarity_score": 0.85
            }
        ]
    },
    "fingerprint.created": {
        "id": 456,
        "video_id": 123,
        "segment_index": 0,
        "start_time": 0,
        "end_time": 90,
        "fingerprint_hash": "abc123def456"
    },
    "channel.ingested": {
        "id": 789,
        "channel_id": "UCtest123",
        "title": "Test Channel",
        "video_count": 150,
        "ingested_videos": 150,
        "failed_videos": 0,
        "processing_time": 1200.5
    },
    "quota.warning": {
        "period": "daily",
        "used": 8500,
        "limit": 10000,
        "remaining": 1500,
        "percentage": 85.0,
        "reset_at": (datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)).isoformat()
    }
}


def generate_signature(payload: bytes, secret: str) -> str:
    """
    Generate HMAC SHA-256 signature for webhook payload.
    
    Args:
        payload: Raw JSON payload as bytes
        secret: Webhook secret key
        
    Returns:
        Hex-encoded signature
    """
    return hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()


def send_webhook_event(
    url: str,
    event_type: str,
    data: Dict[str, Any],
    secret: str,
    webhook_id: str = "wh_test123",
    delivery_id: str = None
) -> requests.Response:
    """
    Send a webhook event to the specified URL.
    
    Args:
        url: Webhook endpoint URL
        event_type: Event type (e.g., 'video.processed')
        data: Event data payload
        secret: Webhook secret for signature
        webhook_id: Webhook identifier
        delivery_id: Unique delivery identifier
        
    Returns:
        Response object
    """
    # Generate delivery ID
    if delivery_id is None:
        delivery_id = f"del_{int(time.time() * 1000)}"
    
    # Build payload
    payload = {
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "webhook_id": webhook_id,
        "delivery_id": delivery_id,
        "data": data
    }
    
    # Convert to JSON
    payload_json = json.dumps(payload, indent=2)
    payload_bytes = payload_json.encode('utf-8')
    
    # Generate signature
    signature = generate_signature(payload_bytes, secret)
    
    # Prepare headers
    headers = {
        'Content-Type': 'application/json',
        'X-Webhook-Signature': signature,
        'X-Webhook-ID': webhook_id,
        'X-Delivery-ID': delivery_id,
        'User-Agent': 'SoundHash-Webhooks/1.0'
    }
    
    # Send request
    print(f"\n📤 Sending webhook event to: {url}")
    print(f"   Event: {event_type}")
    print(f"   Delivery ID: {delivery_id}")
    print(f"   Signature: {signature[:16]}...")
    
    try:
        response = requests.post(
            url,
            data=payload_bytes,
            headers=headers,
            timeout=30
        )
        return response
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
        sys.exit(1)


def verify_response(response: requests.Response):
    """Verify webhook endpoint response."""
    print(f"\n📥 Response received:")
    print(f"   Status: {response.status_code}")
    print(f"   Time: {response.elapsed.total_seconds():.2f}s")
    
    if response.headers:
        print(f"   Headers:")
        for key, value in response.headers.items():
            if key.lower() in ['content-type', 'content-length', 'server']:
                print(f"     {key}: {value}")
    
    if 200 <= response.status_code < 300:
        print(f"\n✅ Webhook endpoint accepted the event!")
        return True
    else:
        print(f"\n❌ Webhook endpoint rejected the event!")
        if response.text:
            print(f"   Response body: {response.text[:200]}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test SoundHash webhook endpoints",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available event types:
  - video.uploaded      Video uploaded
  - video.processing    Video processing started
  - video.processed     Video processing completed
  - video.failed        Video processing failed
  - match.found         Audio match detected
  - fingerprint.created Fingerprint extracted
  - channel.ingested    Channel ingestion completed
  - quota.warning       Approaching quota limit

Examples:
  python scripts/test_webhook.py \\
    --url https://myapp.com/webhooks/soundhash \\
    --event video.processed \\
    --secret my-webhook-secret
  
  python scripts/test_webhook.py \\
    --url http://localhost:3000/webhooks \\
    --event match.found \\
    --secret test-secret \\
    --custom-data '{"query_id": "custom123"}'
"""
    )
    
    parser.add_argument(
        '--url',
        required=True,
        help='Webhook endpoint URL'
    )
    parser.add_argument(
        '--event',
        required=True,
        choices=list(SAMPLE_EVENTS.keys()),
        help='Event type to send'
    )
    parser.add_argument(
        '--secret',
        required=True,
        help='Webhook secret for signature'
    )
    parser.add_argument(
        '--custom-data',
        help='Custom JSON data (overrides sample data)'
    )
    parser.add_argument(
        '--webhook-id',
        default='wh_test123',
        help='Webhook ID (default: wh_test123)'
    )
    parser.add_argument(
        '--delivery-id',
        help='Delivery ID (auto-generated if not provided)'
    )
    
    args = parser.parse_args()
    
    # Get event data
    if args.custom_data:
        try:
            data = json.loads(args.custom_data)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in --custom-data: {e}")
            sys.exit(1)
    else:
        data = SAMPLE_EVENTS[args.event]
    
    print("="*60)
    print("SoundHash Webhook Tester")
    print("="*60)
    
    # Send event
    response = send_webhook_event(
        url=args.url,
        event_type=args.event,
        data=data,
        secret=args.secret,
        webhook_id=args.webhook_id,
        delivery_id=args.delivery_id
    )
    
    # Verify response
    success = verify_response(response)
    
    print("\n" + "="*60)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
