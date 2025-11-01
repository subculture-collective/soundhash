# Getting Started with SoundHash Developer Portal

Welcome! This guide will help you get started with the SoundHash Developer Portal and API.

## 🎯 What You Can Do

SoundHash API enables you to:

- 🎵 **Upload and process videos** to extract audio fingerprints
- 🔍 **Find matches** for audio clips across your video library
- 📺 **Ingest YouTube channels** automatically
- 🎣 **Receive webhooks** for real-time event notifications
- 📊 **Track analytics** and API usage
- 🔐 **Secure access** with JWT or API keys

## 🚀 Quick Start (5 Minutes)

### 1. Get Your API Key

1. Visit [api.soundhash.io/signup](https://api.soundhash.io/signup)
2. Create your account
3. Navigate to **Dashboard → API Keys**
4. Click **Create New Key**
5. Save your key securely!

### 2. Choose Your Language

Pick your preferred language and install the SDK:

=== "Python"
    ```bash
    pip install soundhash-client
    ```

=== "JavaScript"
    ```bash
    npm install @soundhash/client
    ```

=== "TypeScript"
    ```bash
    npm install @soundhash/client-ts
    ```

=== "PHP"
    ```bash
    composer require soundhash/client
    ```

=== "Ruby"
    ```bash
    gem install soundhash-client
    ```

=== "Go"
    ```bash
    go get github.com/subculture-collective/soundhash-client-go
    ```

### 3. Make Your First Request

=== "Python"
    ```python
    from soundhash import ApiClient, Configuration, VideosApi
    
    config = Configuration()
    config.host = "https://api.soundhash.io"
    config.access_token = "YOUR_API_KEY"
    
    with ApiClient(config) as client:
        api = VideosApi(client)
        videos = api.list_videos(limit=5)
        
        for video in videos:
            print(f"{video.title} - {video.duration}s")
    ```

=== "JavaScript"
    ```javascript
    const SoundHash = require('@soundhash/client');
    
    const client = new SoundHash.ApiClient();
    client.basePath = 'https://api.soundhash.io';
    client.authentications['bearerAuth'].accessToken = 'YOUR_API_KEY';
    
    const api = new SoundHash.VideosApi(client);
    
    api.listVideos({ limit: 5 }, (error, videos) => {
      if (error) console.error(error);
      else videos.forEach(v => console.log(`${v.title} - ${v.duration}s`));
    });
    ```

=== "cURL"
    ```bash
    curl -X GET "https://api.soundhash.io/api/v1/videos?limit=5" \
      -H "Authorization: Bearer YOUR_API_KEY"
    ```

That's it! You've made your first API call! 🎉

## 📚 What's Next?

### Core Guides

1. **[Quick Start Tutorial](tutorials/quickstart.md)** - Complete walkthrough in 5 minutes
2. **[Authentication](authentication.md)** - Learn about JWT and API keys
3. **[Rate Limits](rate-limits.md)** - Understanding quotas and best practices
4. **[Webhooks](webhooks/index.md)** - Set up event notifications

### Common Use Cases

- **[Content ID System](tutorials/content-id.md)** - Detect audio in videos
- **[Social Media Bot](tutorials/social-bot.md)** - Build a Twitter/Discord bot
- **[Music Recognition](tutorials/shazam-clone.md)** - Create a Shazam-like app
- **[Copyright Detection](tutorials/copyright.md)** - Find unauthorized use

### Resources

- 📖 **[API Reference](reference.md)** - Complete endpoint documentation
- 💻 **[Code Examples](code-examples/)** - Copy-paste examples in 6 languages
- 📮 **[Postman Collection](postman_collection.json)** - Import for testing
- 🔧 **[Developer Tools](DEVELOPER_TOOLS.md)** - SDK generation and more

### Interactive Playground

- **[Swagger UI](https://api.soundhash.io/docs)** - Try all endpoints interactively
- **[ReDoc](https://api.soundhash.io/redoc)** - Beautiful API documentation

## 🎯 Popular Endpoints

### Upload a Video

```bash
curl -X POST "https://api.soundhash.io/api/v1/videos" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@video.mp4" \
  -F "title=My Video"
```

### Find Audio Matches

```bash
curl -X POST "https://api.soundhash.io/api/v1/matches/find" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "audio_file=@clip.wav" \
  -F "min_confidence=0.8"
```

### Create a Webhook

```bash
curl -X POST "https://api.soundhash.io/api/v1/webhooks" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://myapp.com/webhook",
    "events": ["video.processed"],
    "secret": "my-secret"
  }'
```

## 💡 Tips & Best Practices

### Rate Limiting

- Start with the **Free tier** (60 req/min)
- Implement **exponential backoff** for retries
- Cache responses when possible
- Use **webhooks** instead of polling

### Authentication

- Use **API keys** for server-to-server
- Use **JWT tokens** for user applications
- Never commit credentials to git
- Rotate keys regularly

### Error Handling

- Check response status codes
- Read error messages carefully
- Log failed requests for debugging
- Implement retry logic for transient errors

### Performance

- Use **batch endpoints** when available
- Enable **caching** for repeated queries
- Process videos **asynchronously**
- Monitor your **quota usage**

## 🆘 Need Help?

### Documentation

- 📖 [Full API Documentation](index.md)
- 🚀 [Quick Start Tutorial](tutorials/quickstart.md)
- 💻 [Code Examples](code-examples/)
- 🔧 [Developer Tools](DEVELOPER_TOOLS.md)

### Support Channels

- 💬 [GitHub Discussions](https://github.com/subculture-collective/soundhash/discussions)
- 🐛 [Report a Bug](https://github.com/subculture-collective/soundhash/issues)
- 💡 [Feature Requests](https://github.com/subculture-collective/soundhash/issues/new?template=feature_request.md)
- 📧 [Email Support](mailto:support@soundhash.io)
- 💬 [Discord Community](https://discord.gg/soundhash)

### Status & Monitoring

- 🟢 [API Status](https://status.soundhash.io)
- 📊 [System Metrics](https://api.soundhash.io/api/v1/monitoring/metrics)
- 📈 [Your Usage](https://api.soundhash.io/dashboard)

## 📱 Stay Updated

- 🐦 Follow [@SoundHashDev](https://twitter.com/SoundHashDev) on Twitter
- ⭐ Star us on [GitHub](https://github.com/subculture-collective/soundhash)
- 📰 Subscribe to [API Changelog](changelog.md)
- 💬 Join our [Discord](https://discord.gg/soundhash)

## 🎉 Ready to Build?

You're all set! Here's what to do next:

1. ✅ Check out the [Quick Start Tutorial](tutorials/quickstart.md)
2. ✅ Try the [Interactive Playground](https://api.soundhash.io/docs)
3. ✅ Download the [Postman Collection](postman_collection.json)
4. ✅ Join our [Discord Community](https://discord.gg/soundhash)

Happy coding! 🚀
