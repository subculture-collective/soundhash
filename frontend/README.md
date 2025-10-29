# SoundHash Frontend

Modern, responsive React/Next.js frontend application for SoundHash audio fingerprinting and matching system.

## 🚀 Features

- ✨ **Modern UI/UX** - Beautiful, intuitive interface built with Next.js 14+ and Tailwind CSS
- 🎨 **Dark/Light Theme** - Automatic theme switching with system preference detection
- 📱 **Responsive Design** - Optimized for mobile, tablet, and desktop
- ⚡ **Server-Side Rendering** - Fast page loads with Next.js SSR
- 🔐 **Authentication** - Secure login, registration, and password reset
- 📤 **Drag & Drop Upload** - Easy audio/video file uploads
- 🎵 **Audio Visualization** - Waveform display with WaveSurfer.js
- 🔄 **Real-time Updates** - WebSocket support for live match results
- 📊 **User Dashboard** - Match history, statistics, and analytics
- ♿ **Accessibility** - WCAG 2.1 AA compliant
- 🌐 **PWA Support** - Install as app, offline capability

## 📋 Prerequisites

- Node.js 18+ and npm
- Backend API running (see main README)

## 🛠️ Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local

# Edit .env.local with your API URL
nano .env.local
```

## 🔧 Configuration

Edit `.env.local`:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# App Configuration
NEXT_PUBLIC_APP_NAME=SoundHash
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## 🚦 Development

```bash
# Start development server
npm run dev

# Open browser to http://localhost:3000
```

## 🏗️ Build for Production

```bash
# Build optimized production bundle
npm run build

# Start production server
npm start
```

## 📦 Project Structure

```
frontend/
├── app/                      # Next.js app directory (routes)
│   ├── auth/                # Authentication pages
│   │   ├── login/           # Login page
│   │   ├── register/        # Registration page
│   │   └── reset-password/  # Password reset
│   ├── dashboard/           # Dashboard pages (future)
│   ├── layout.tsx           # Root layout with providers
│   ├── page.tsx             # Landing page
│   └── globals.css          # Global styles
├── components/              # React components
│   ├── ui/                  # Reusable UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── badge.tsx
│   ├── features/            # Feature-specific components
│   │   └── audio/           # Audio-related components
│   │       └── AudioUploader.tsx
│   ├── landing/             # Landing page sections
│   │   ├── Hero.tsx
│   │   ├── Features.tsx
│   │   ├── HowItWorks.tsx
│   │   └── CTA.tsx
│   └── theme-provider.tsx   # Theme context provider
├── lib/                     # Utility libraries
│   ├── api.ts              # API client with auth
│   └── utils.ts            # Helper functions
├── store/                   # State management
│   └── authStore.ts        # Zustand auth store
├── public/                  # Static assets
│   └── manifest.json       # PWA manifest
└── package.json
```

## 🎨 Technology Stack

### Core
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4

### UI Components
- **Component Library**: Radix UI primitives
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **Notifications**: Sonner

### State & Data
- **State Management**: Zustand with persist
- **API Client**: Axios
- **Data Fetching**: TanStack React Query

### Audio & Visualization
- **Audio Player**: WaveSurfer.js
- **Charts**: Recharts
- **File Upload**: React Dropzone

## 🔑 Key Features

### Authentication
- Login/register with JWT tokens
- Automatic token refresh
- Protected routes
- Remember me functionality

### Audio Upload
- Drag and drop interface
- Progress tracking
- File type validation
- Size limits (100MB)

### Theme Support
- Light/dark mode
- System preference detection
- Persistent user choice

## 📱 PWA Features

- Installable on mobile/desktop
- Offline support
- App manifest
- Service worker (future)

## ♿ Accessibility

- Semantic HTML
- ARIA labels
- Keyboard navigation
- Screen reader support
- WCAG 2.1 AA compliance

## 🐛 Troubleshooting

### API Connection Issues
```bash
# Check API is running
curl http://localhost:8000/api/v1/health

# Verify CORS settings in backend
API_CORS_ORIGINS=http://localhost:3000
```

### Build Errors
```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

## 🔗 Related Documentation

- [Main README](../README.md)
- [API Documentation](../docs/API.md)
- [Backend Setup](../INSTALL.md)
