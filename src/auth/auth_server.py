from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
import tweepy
import urllib.parse
import logging
from config.settings import Config
import uuid
import json
from typing import Dict

app = FastAPI(title="SoundHash Authentication Server")
logger = logging.getLogger(__name__)

# Store OAuth states temporarily (in production, use Redis or database)
oauth_states: Dict[str, dict] = {}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "SoundHash Authentication Server", "status": "running"}

@app.get("/auth/twitter")
async def twitter_auth():
    """Initiate Twitter OAuth flow"""
    try:
        # Create OAuth 1.0a handler
        auth = tweepy.OAuth1UserHandler(
            Config.TWITTER_CONSUMER_KEY,
            Config.TWITTER_CONSUMER_SECRET,
            callback=f"{Config.CALLBACK_BASE_URL}/auth/twitter/callback"
        )
        
        # Get authorization URL
        authorization_url = auth.get_authorization_url()
        
        # Store request token for callback
        state = str(uuid.uuid4())
        oauth_states[state] = {
            'request_token': auth.request_token,
            'platform': 'twitter'
        }
        
        # Redirect to Twitter
        return RedirectResponse(url=f"{authorization_url}&state={state}")
        
    except Exception as e:
        logger.error(f"Error initiating Twitter auth: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate Twitter authentication")

@app.get("/auth/twitter/callback")
async def twitter_callback(oauth_token: str, oauth_verifier: str, state: str = None):
    """Handle Twitter OAuth callback"""
    try:
        if not state or state not in oauth_states:
            raise HTTPException(status_code=400, detail="Invalid or expired state")
        
        oauth_data = oauth_states.pop(state)
        
        # Complete OAuth flow
        auth = tweepy.OAuth1UserHandler(
            Config.TWITTER_CONSUMER_KEY,
            Config.TWITTER_CONSUMER_SECRET
        )
        
        auth.request_token = oauth_data['request_token']
        access_token, access_token_secret = auth.get_access_token(oauth_verifier)
        
        # Get user info
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)
        user = api.verify_credentials()
        
        # Store credentials (in production, store securely)
        auth_result = {
            "platform": "twitter",
            "user_id": user.id,
            "username": user.screen_name,
            "display_name": user.name,
            "access_token": access_token,
            "access_token_secret": access_token_secret,
            "profile_image": user.profile_image_url_https
        }
        
        # Return success page with credentials
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Twitter Authentication Successful</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .success {{ color: green; }}
                .credentials {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .warning {{ color: #ff6600; font-weight: bold; }}
                code {{ background: #eee; padding: 2px 4px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <h1 class="success">✅ Twitter Authentication Successful!</h1>
            <p>Hello <strong>{user.name}</strong> (@{user.screen_name})!</p>
            
            <h2>Your Credentials:</h2>
            <div class="credentials">
                <p><strong>Access Token:</strong><br><code>{access_token}</code></p>
                <p><strong>Access Token Secret:</strong><br><code>{access_token_secret}</code></p>
            </div>
            
            <p class="warning">⚠️ Keep these credentials secure! Add them to your .env file:</p>
            <div class="credentials">
                <code>TWITTER_ACCESS_TOKEN={access_token}</code><br>
                <code>TWITTER_ACCESS_TOKEN_SECRET={access_token_secret}</code>
            </div>
            
            <p>You can now close this window and restart your SoundHash services.</p>
        </body>
        </html>
        """)
        
    except Exception as e:
        logger.error(f"Error in Twitter callback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to complete Twitter authentication")

@app.get("/auth/reddit")
async def reddit_auth():
    """Initiate Reddit OAuth flow"""
    try:
        import praw
        
        reddit = praw.Reddit(
            client_id=Config.REDDIT_CLIENT_ID,
            client_secret=Config.REDDIT_CLIENT_SECRET,
            redirect_uri=f"{Config.CALLBACK_BASE_URL}/auth/reddit/callback",
            user_agent=Config.REDDIT_USER_AGENT
        )
        
        state = str(uuid.uuid4())
        oauth_states[state] = {'platform': 'reddit'}
        
        scopes = ['identity', 'read', 'submit']
        auth_url = reddit.auth.url(scopes, state, duration='permanent')
        
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error(f"Error initiating Reddit auth: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate Reddit authentication")

@app.get("/auth/reddit/callback")
async def reddit_callback(code: str, state: str):
    """Handle Reddit OAuth callback"""
    try:
        if not state or state not in oauth_states:
            raise HTTPException(status_code=400, detail="Invalid or expired state")
        
        oauth_states.pop(state)
        
        import praw
        
        reddit = praw.Reddit(
            client_id=Config.REDDIT_CLIENT_ID,
            client_secret=Config.REDDIT_CLIENT_SECRET,
            redirect_uri=f"{Config.CALLBACK_BASE_URL}/auth/reddit/callback",
            user_agent=Config.REDDIT_USER_AGENT
        )
        
        refresh_token = reddit.auth.authorize(code)
        user = reddit.user.me()
        
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Reddit Authentication Successful</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .success {{ color: green; }}
                .credentials {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .warning {{ color: #ff6600; font-weight: bold; }}
                code {{ background: #eee; padding: 2px 4px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <h1 class="success">✅ Reddit Authentication Successful!</h1>
            <p>Hello <strong>u/{user.name}</strong>!</p>
            
            <h2>Your Credentials:</h2>
            <div class="credentials">
                <p><strong>Refresh Token:</strong><br><code>{refresh_token}</code></p>
            </div>
            
            <p class="warning">⚠️ Keep this refresh token secure! Add it to your .env file:</p>
            <div class="credentials">
                <code>REDDIT_REFRESH_TOKEN={refresh_token}</code>
            </div>
            
            <p>You can now close this window and restart your SoundHash services.</p>
        </body>
        </html>
        """)
        
    except Exception as e:
        logger.error(f"Error in Reddit callback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to complete Reddit authentication")

@app.get("/auth/status")
async def auth_status():
    """Check authentication status"""
    try:
        status = {
            "twitter": {
                "configured": bool(Config.TWITTER_CONSUMER_KEY and Config.TWITTER_CONSUMER_SECRET),
                "authenticated": bool(Config.TWITTER_ACCESS_TOKEN and Config.TWITTER_ACCESS_TOKEN_SECRET)
            },
            "reddit": {
                "configured": bool(Config.REDDIT_CLIENT_ID and Config.REDDIT_CLIENT_SECRET),
                "authenticated": bool(getattr(Config, 'REDDIT_REFRESH_TOKEN', None))
            },
            "youtube": {
                "configured": bool(Config.YOUTUBE_API_KEY)
            }
        }
        return status
    except Exception as e:
        logger.error(f"Error checking auth status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check authentication status")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)