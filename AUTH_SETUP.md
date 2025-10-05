# OAuth Authentication Setup Guide

This guide will help you set up OAuth authentication for Twitter and Reddit using the SoundHash authentication server.

## Prerequisites

1. Twitter Developer Account
2. Reddit App (for Reddit integration)
3. SoundHash Docker environment running

## Twitter OAuth Setup

### 1. Create Twitter App

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a new project/app
3. Navigate to app settings → Authentication settings
4. Enable OAuth 1.0a
5. Add callback URL: `http://localhost:8000/auth/twitter/callback`
6. Note down your API Key and API Secret Key

### 2. Configure Environment

Add your Twitter credentials to `.env.docker`:

```env
TWITTER_CONSUMER_KEY=your_api_key_here
TWITTER_CONSUMER_SECRET=your_api_secret_key_here
```

### 3. Start Authentication Server

```bash
./docker/manage.sh auth
```

### 4. Authenticate

1. Open browser to: http://localhost:8000/auth/twitter
2. Authorize the application on Twitter
3. Copy the returned access tokens
4. Add tokens to `.env.docker`:

```env
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

## Reddit OAuth Setup

### 1. Create Reddit App

1. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App"
3. Choose "script" type
4. Add redirect URI: `http://localhost:8000/auth/reddit/callback`
5. Note down your client ID and secret

### 2. Configure Environment

Add your Reddit credentials to `.env.docker`:

```env
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
```

### 3. Authenticate

1. Open browser to: http://localhost:8000/auth/reddit
2. Authorize the application on Reddit
3. Copy the returned refresh token
4. Add token to `.env.docker`:

```env
REDDIT_REFRESH_TOKEN=your_refresh_token_here
```

## Verification

Check your authentication status:

```bash
curl http://localhost:8000/auth/status
```

This will show which platforms are configured and authenticated.

## Production Considerations

For production deployment:

1. **Use HTTPS**: Change `CALLBACK_BASE_URL` to use HTTPS
2. **Secure Storage**: Store tokens in a secure key management system
3. **Environment Variables**: Use proper secrets management
4. **Domain**: Use your actual domain instead of localhost
5. **Firewall**: Restrict access to the auth server

Example production configuration:

```env
CALLBACK_BASE_URL=https://yourdomain.com
AUTH_SERVER_HOST=0.0.0.0
AUTH_SERVER_PORT=8000
```

Update your app callback URLs accordingly:

-   Twitter: `https://yourdomain.com/auth/twitter/callback`
-   Reddit: `https://yourdomain.com/auth/reddit/callback`

## Troubleshooting

### Common Issues

**"Invalid callback URL" error:**

-   Ensure the callback URL in your app settings exactly matches the one configured
-   Check for typos in the URL
-   Verify the authentication server is accessible

**"Application not authorized" error:**

-   Check your API keys are correct
-   Ensure your app has the necessary permissions
-   Verify the app is not suspended

**Authentication server not starting:**

-   Check Docker logs: `./docker/manage.sh logs soundhash_auth_server`
-   Verify port 8000 is not in use by another service
-   Check environment variables are properly set

### Debug Mode

To run the authentication server with debug logging:

```bash
# Modify docker-compose.yml command temporarily:
command: ["python", "-m", "uvicorn", "src.auth.auth_server:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]
```

## Security Notes

-   Keep your API keys and tokens secure
-   Never commit authentication credentials to version control
-   Use environment variables or secure key management in production
-   Regularly rotate your API keys and tokens
-   Monitor for unauthorized access to your applications
