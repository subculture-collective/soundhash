# YouTube Data API v3 OAuth Setup

## Overview

The system now uses YouTube Data API v3 for metadata retrieval to avoid bot detection issues with yt-dlp. This requires OAuth 2.0 authentication.

## Setup Steps

### 1. Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **YouTube Data API v3**:
    - Go to "APIs & Services" > "Library"
    - Search for "YouTube Data API v3"
    - Click "Enable"

### 2. Configure OAuth Consent Screen

**IMPORTANT**: You must configure the OAuth consent screen before creating credentials.

1. Go to "APIs & Services" > "OAuth consent screen"
2. **Choose "External"** (unless you have Google Workspace)
3. Fill in required fields:
    - **App name**: "SoundHash"
    - **User support email**: Your email
    - **Developer contact email**: Your email
4. **Scopes**: Add `https://www.googleapis.com/auth/youtube.readonly`
5. **Test users**: Add your own Google account email
6. Click "Save and Continue"

**Note**: In testing mode, only test users you specify can use the app. This is normal for development.

### 3. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. **Important**: Choose "**Desktop Application**" as the application type
4. Give it a name (e.g., "SoundHash YouTube Access")
5. **Add Authorized redirect URIs** (click "ADD URI" and add these):
    - `http://localhost:8080/`
    - `http://localhost:8000/`
    - `http://localhost/`
6. Click "Create"

**Note**: Even desktop applications need redirect URIs configured for the OAuth flow to work properly.

### 3. Download Credentials

1. Download the JSON file from the credentials page
2. Save it as `credentials.json` in the project root directory
3. Keep this file secure and don't commit it to version control

### 4. Test the Setup

```bash
python scripts/setup_youtube_api.py
```

This will:

-   Check for credentials.json
-   Run OAuth flow (opens browser for consent)
-   Test API connectivity
-   Save refresh token for future use

## Authentication Flow

### First Time Setup

1. Script opens browser for Google OAuth consent
2. User grants permissions to access YouTube data
3. Google redirects to a temporary localhost server (started automatically)
4. Refresh token is saved to `token.json`

**Note**: The browser will show "The authentication flow has completed" or similar when successful.

### Subsequent Runs

1. System uses saved refresh token
2. Automatically refreshes expired access tokens
3. No user interaction needed

## API Quotas and Limits

### YouTube Data API v3 Quotas (per day):

-   **Default**: 10,000 units
-   **Channel list**: ~3 units per request
-   **Video details**: ~1 unit per video
-   **Playlist items**: ~1 unit per request

### Estimated Usage:

-   **3 channels, 50 videos each**: ~200 units per run
-   **Daily runs**: Fits comfortably within quota

## Fallback Strategy

If YouTube Data API fails:

1. System falls back to yt-dlp with browser cookies
2. Manual cookie export may be needed:
    ```bash
    yt-dlp --cookies-from-browser chrome --extract-audio URL
    ```

## Benefits of API Approach

### ✅ Advantages:

-   No bot detection issues
-   Reliable metadata access
-   Official Google-supported method
-   Structured data format
-   Rate limiting instead of blocking

### ⚠️ Considerations:

-   Requires OAuth setup
-   API quota limits (generous for our use)
-   Cannot download audio directly (still need yt-dlp for audio)

## Troubleshooting

### Common Issues:

**"Error 403: access_denied" - App in Testing Mode**

This means your OAuth consent screen is in "Testing" mode and you haven't added yourself as a test user.

**Solution**:

1. Go to Google Cloud Console > APIs & Services > OAuth consent screen
2. Click "ADD USERS" in the Test users section
3. Add your Google account email address
4. Save and try the OAuth flow again

**Alternative**: Change to "External" user type if you want anyone to access (requires verification for production use)

**"redirect_uri_mismatch" Error**

-   Go to Google Cloud Console > APIs & Services > Credentials
-   Edit your OAuth 2.0 Client ID
-   Add these redirect URIs:
    -   `http://localhost:8080/`
    -   `http://localhost:8000/`
    -   `http://localhost/`
-   Save and try again

**"Credentials file not found"**

-   Ensure `credentials.json` is in project root
-   Check file permissions

**"API not enabled"**

-   Verify YouTube Data API v3 is enabled in Google Cloud Console

**"Quota exceeded"**

-   Wait until quota resets (daily)
-   Consider requesting quota increase

**"Invalid credentials"**

-   Re-download credentials.json
-   Delete token.json and re-authenticate

## Files Created:

-   `credentials.json` - OAuth client credentials (download from Google)
-   `token.json` - Refresh token (generated during first auth)

## Security Notes:

-   Keep `credentials.json` secure
-   Add both files to `.gitignore`
-   Don't share credentials or tokens
-   Revoke access in Google Cloud Console if compromised
