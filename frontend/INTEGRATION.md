# Frontend Integration Guide

This guide explains how to integrate the SoundHash frontend with the backend API.

## 📋 Overview

The frontend communicates with the backend through:
- REST API endpoints (`/api/v1/`)
- WebSocket connections (future) (`/ws`)
- File uploads (multipart/form-data)

## 🔗 API Integration

### Authentication

The frontend uses JWT tokens for authentication.

**Login Flow:**
```typescript
// 1. User submits credentials
POST /api/v1/auth/login
{
  "username": "user",
  "password": "password"
}

// 2. Backend responds with tokens
{
  "user": { "id": "...", "username": "user", "email": "..." },
  "access_token": "eyJ...",
  "refresh_token": "eyJ..."
}

// 3. Frontend stores tokens
localStorage.setItem('access_token', access_token)
localStorage.setItem('refresh_token', refresh_token)

// 4. All subsequent requests include Authorization header
Authorization: Bearer eyJ...
```

**Token Refresh:**
```typescript
// When access token expires (401 error)
POST /api/v1/auth/refresh
{
  "refresh_token": "eyJ..."
}

// Backend responds with new access token
{
  "access_token": "eyJ..."
}
```

Implementation in `frontend/lib/api.ts`:
```typescript
// Interceptor automatically adds auth header
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Interceptor automatically refreshes on 401
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Refresh token and retry request
    }
  }
)
```

### File Upload

The frontend uploads audio/video files for matching.

**Upload Flow:**
```typescript
// 1. User drops file or selects via file picker
const formData = new FormData()
formData.append('file', file)

// 2. POST to upload endpoint with progress tracking
POST /api/v1/videos/upload
Content-Type: multipart/form-data

{
  onUploadProgress: (progressEvent) => {
    const percent = (progressEvent.loaded * 100) / progressEvent.total
    // Update UI with progress
  }
}

// 3. Backend processes and responds
{
  "video_id": "...",
  "filename": "...",
  "status": "processing",
  "job_id": "..."
}

// 4. Frontend polls or receives WebSocket updates
```

Implementation in `frontend/components/features/audio/AudioUploader.tsx`.

### Match Results

The frontend queries for match results.

**Query Flow:**
```typescript
// 1. Get matches for uploaded video
GET /api/v1/matches/video/{video_id}

// 2. Backend responds with matches
{
  "matches": [
    {
      "id": "...",
      "title": "Video Title",
      "channel_name": "Channel Name",
      "video_url": "https://youtube.com/watch?v=...",
      "confidence": 0.95,
      "start_time": 10.5,
      "end_time": 20.3,
      "view_count": 1000000,
      "thumbnail_url": "https://..."
    }
  ],
  "total": 1
}
```

Implementation in `frontend/components/features/matching/MatchResults.tsx`.

## 🔌 Backend Requirements

### CORS Configuration

The backend must allow requests from the frontend origin.

**Backend .env:**
```bash
API_CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

**FastAPI setup (should already be configured):**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.API_CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API Endpoints Required

The frontend expects these endpoints:

**Authentication:**
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `GET /api/v1/auth/me` - Get current user

**Videos:**
- `POST /api/v1/videos/upload` - Upload audio/video file
- `GET /api/v1/videos` - List user's videos
- `GET /api/v1/videos/{id}` - Get video details

**Matches:**
- `GET /api/v1/matches/video/{id}` - Get matches for video
- `GET /api/v1/matches` - List all matches
- `GET /api/v1/matches/{id}` - Get match details

**Fingerprints:**
- `GET /api/v1/fingerprints/{id}` - Get fingerprint data

**User:**
- `GET /api/v1/users/me` - Get user profile
- `GET /api/v1/users/me/stats` - Get user statistics
- `PUT /api/v1/users/me` - Update user profile

### Response Format

All API responses should follow this format:

**Success:**
```json
{
  "data": { ... },
  "message": "Success",
  "status": 200
}
```

**Error:**
```json
{
  "detail": "Error message",
  "status": 400
}
```

## 🚀 Running Together

### Development Setup

**Terminal 1 - Backend:**
```bash
# From project root
python scripts/start_api.py

# Or with Docker
docker compose up
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - Database (if not using Docker):**
```bash
# Ensure PostgreSQL is running
sudo systemctl start postgresql
# or
brew services start postgresql
```

### Environment Configuration

**Backend `.env`:**
```bash
# API
API_HOST=0.0.0.0
API_PORT=8000
API_CORS_ORIGINS=http://localhost:3000

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/soundhash

# Auth
API_SECRET_KEY=your-secret-key
```

**Frontend `.env.local`:**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

### Testing the Integration

1. **Start Backend:**
   ```bash
   python scripts/start_api.py
   # Check: curl http://localhost:8000/health
   ```

2. **Start Frontend:**
   ```bash
   cd frontend && npm run dev
   # Visit: http://localhost:3000
   ```

3. **Test Authentication:**
   - Click "Get Started" or "Sign In"
   - Register a new user
   - Verify you're redirected to dashboard
   - Check browser console for any errors

4. **Test File Upload:**
   - Go to Dashboard
   - Drag and drop an audio file
   - Watch progress bar
   - Check backend logs for upload processing

5. **Test API Calls:**
   ```bash
   # Check browser Network tab in DevTools
   # Should see requests to http://localhost:8000/api/v1/
   ```

## 🔧 Troubleshooting

### CORS Errors

**Symptom:**
```
Access to XMLHttpRequest at 'http://localhost:8000/api/v1/auth/login' 
from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Solution:**
1. Check backend CORS configuration
2. Verify `API_CORS_ORIGINS` includes frontend URL
3. Restart backend after changing environment variables

### 401 Unauthorized

**Symptom:**
All API requests return 401 even with valid token.

**Solution:**
1. Check token in localStorage: `localStorage.getItem('access_token')`
2. Verify token format in Authorization header
3. Check backend JWT secret key configuration
4. Ensure tokens haven't expired

### File Upload Fails

**Symptom:**
Upload progress reaches 100% but gets error response.

**Solution:**
1. Check file size (< 100MB)
2. Verify file type is supported
3. Check backend `MAX_FILE_SIZE` setting
4. Review backend logs for processing errors
5. Ensure temp directory exists and is writable

### Network Errors

**Symptom:**
`ERR_CONNECTION_REFUSED` or `Network Error`

**Solution:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `NEXT_PUBLIC_API_URL` in `.env.local`
3. Ensure ports are not blocked by firewall
4. Try restarting both frontend and backend

## 📊 API Call Flow Diagram

```
Frontend                Backend                 Database
   |                       |                        |
   |  POST /auth/login     |                        |
   |---------------------->|                        |
   |                       |  Query user            |
   |                       |----------------------->|
   |                       |<-----------------------|
   |  200 + tokens         |                        |
   |<----------------------|                        |
   |                       |                        |
   |  POST /videos/upload  |                        |
   |  (with auth header)   |                        |
   |---------------------->|                        |
   |                       |  Create video record   |
   |                       |----------------------->|
   |                       |<-----------------------|
   |                       |  Queue processing job  |
   |  202 + video_id       |----------------------->|
   |<----------------------|                        |
   |                       |                        |
   | (Wait for processing) |                        |
   |                       |  Process audio         |
   |                       |  Extract fingerprints  |
   |                       |  Find matches          |
   |                       |----------------------->|
   |                       |<-----------------------|
   |                       |                        |
   |  GET /matches/{id}    |                        |
   |---------------------->|                        |
   |                       |  Query matches         |
   |                       |----------------------->|
   |                       |<-----------------------|
   |  200 + matches        |                        |
   |<----------------------|                        |
```

## 🌐 WebSocket Integration (Future)

**Plan for real-time updates:**

```typescript
// frontend/hooks/useWebSocket.ts
const socket = new WebSocket('ws://localhost:8000/ws')

socket.onmessage = (event) => {
  const data = JSON.parse(event.data)
  
  switch(data.type) {
    case 'upload_progress':
      // Update upload progress UI
      break
    case 'processing_complete':
      // Refresh matches
      break
    case 'match_found':
      // Show notification
      break
  }
}
```

**Backend WebSocket endpoint:**
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Send updates to connected clients
```

## 📝 Checklist

Before deploying:

- [ ] Backend CORS configured with frontend URL
- [ ] All required API endpoints implemented
- [ ] JWT authentication working
- [ ] File upload handling configured
- [ ] Database migrations run
- [ ] Environment variables set
- [ ] Integration tested end-to-end
- [ ] Error handling tested
- [ ] Performance optimized
- [ ] Logs configured for debugging

## 🔗 Resources

- [Backend API Documentation](../docs/API.md)
- [Frontend README](README.md)
- [Backend Setup Guide](../INSTALL.md)
- [Deployment Guide](DEPLOYMENT.md)
