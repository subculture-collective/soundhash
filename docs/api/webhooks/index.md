# Webhooks

Webhooks allow your application to receive real-time notifications when events occur in SoundHash. Instead of polling the API, webhooks push data to your server as events happen.

## Overview

When an event occurs (e.g., a video is processed), SoundHash sends an HTTP POST request to your configured webhook URL with details about the event.

## Quick Start

### 1. Create a Webhook Endpoint

Create an endpoint in your application to receive webhook events:

=== "Python (Flask)"
    ```python
    from flask import Flask, request
    import hmac
    import hashlib
    
    app = Flask(__name__)
    
    @app.route('/webhooks/soundhash', methods=['POST'])
    def handle_webhook():
        # Verify signature
        signature = request.headers.get('X-Webhook-Signature')
        secret = 'your-webhook-secret'
        
        computed_signature = hmac.new(
            secret.encode(),
            request.data,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, computed_signature):
            return 'Invalid signature', 401
        
        # Process event
        event = request.json
        event_type = event['event']
        
        if event_type == 'video.processed':
            video = event['data']
            print(f"Video processed: {video['title']}")
        
        return '', 200
    ```

=== "Node.js (Express)"
    ```javascript
    const express = require('express');
    const crypto = require('crypto');
    
    const app = express();
    
    // Use express.raw() for webhook route to preserve original body for signature verification
    app.post('/webhooks/soundhash', express.raw({ type: 'application/json' }), (req, res) => {
      // Verify signature using raw body
      const signature = req.headers['x-webhook-signature'];
      const secret = 'your-webhook-secret';
      
      const computedSignature = crypto
        .createHmac('sha256', secret)
        .update(req.body)  // req.body is a Buffer with raw bytes
        .digest('hex');
      
      if (signature !== computedSignature) {
        return res.status(401).send('Invalid signature');
      }
      
      // Parse JSON body after verifying signature
      const { event, data } = JSON.parse(req.body.toString('utf8'));
      
      if (event === 'video.processed') {
        console.log(`Video processed: ${data.title}`);
      }
      
      res.status(200).send();
    });
    
    app.listen(3000);
    ```

### 2. Register Your Webhook

```python
from soundhash import WebhooksApi

webhooks = WebhooksApi(client)
webhook = webhooks.create_webhook(
    url='https://myapp.com/webhooks/soundhash',
    events=['video.processed', 'match.found'],
    secret='your-webhook-secret'
)
```

See the [full webhooks documentation](testing.md) for complete details on testing, security, and troubleshooting.
