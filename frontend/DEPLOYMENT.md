# Frontend Deployment Guide

This guide covers deploying the SoundHash frontend to various platforms.

## 📋 Pre-Deployment Checklist

- [ ] Environment variables configured
- [ ] Backend API is accessible
- [ ] CORS configured on backend
- [ ] Build succeeds locally (`npm run build`)
- [ ] All tests pass (if applicable)
- [ ] Performance optimized (Lighthouse check)

## 🚀 Deployment Options

### Option 1: Vercel (Recommended)

Vercel is the easiest way to deploy Next.js applications.

#### Quick Deploy

1. **Push to GitHub** (already done if using this PR)

2. **Import to Vercel**
   ```bash
   # Install Vercel CLI
   npm i -g vercel
   
   # Login
   vercel login
   
   # Deploy
   cd frontend
   vercel
   ```

3. **Set Environment Variables** in Vercel Dashboard:
   - `NEXT_PUBLIC_API_URL` = Your backend API URL
   - `NEXT_PUBLIC_WS_URL` = Your WebSocket URL

4. **Configure Build Settings**:
   - Framework Preset: Next.js
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `.next`

#### Automatic Deployments

Vercel automatically deploys:
- **Production**: Pushes to `main` branch
- **Preview**: Pushes to other branches and PRs

### Option 2: Docker

Deploy using Docker containers.

#### Create Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build args for environment variables
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_WS_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL

RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000

CMD ["node", "server.js"]
```

#### Update next.config.ts

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  // ... other config
};

export default nextConfig;
```

#### Build and Run

```bash
# Build image
docker build -t soundhash-frontend \
  --build-arg NEXT_PUBLIC_API_URL=http://api.yourdomain.com/api/v1 \
  --build-arg NEXT_PUBLIC_WS_URL=ws://api.yourdomain.com/ws \
  .

# Run container
docker run -p 3000:3000 soundhash-frontend
```

#### Docker Compose

```yaml
# docker-compose.yml (add to root)
services:
  frontend:
    build:
      context: ./frontend
      args:
        NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL}
        NEXT_PUBLIC_WS_URL: ${NEXT_PUBLIC_WS_URL}
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    restart: unless-stopped
```

### Option 3: Netlify

1. **Connect Repository**
   - Go to https://app.netlify.com
   - Click "Add new site" → "Import an existing project"
   - Choose your GitHub repository

2. **Configure Build**
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Publish directory: `.next`
   - Functions directory: (leave empty)

3. **Set Environment Variables**
   - `NEXT_PUBLIC_API_URL`
   - `NEXT_PUBLIC_WS_URL`

4. **Deploy**
   - Click "Deploy site"

### Option 4: AWS (Amplify / EC2)

#### AWS Amplify

1. **Connect Repository**
   - Open AWS Amplify Console
   - Connect to GitHub repository
   - Select branch

2. **Configure**
   ```yaml
   version: 1
   frontend:
     phases:
       preBuild:
         commands:
           - cd frontend
           - npm ci
       build:
         commands:
           - npm run build
     artifacts:
       baseDirectory: frontend/.next
       files:
         - '**/*'
     cache:
       paths:
         - frontend/node_modules/**/*
   ```

3. **Environment Variables**
   - Add in Amplify Console

#### AWS EC2

1. **Launch EC2 Instance**
   - Ubuntu 22.04 LTS
   - t2.medium or larger
   - Open ports: 80, 443, 3000

2. **Setup Server**
   ```bash
   # SSH into instance
   ssh -i your-key.pem ubuntu@your-instance-ip
   
   # Install Node.js
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
   sudo apt-get install -y nodejs
   
   # Install Nginx
   sudo apt-get install -y nginx
   
   # Clone repository
   git clone <your-repo>
   cd soundhash/frontend
   
   # Install dependencies
   npm install
   
   # Build
   npm run build
   
   # Install PM2
   sudo npm install -g pm2
   
   # Start with PM2
   pm2 start npm --name "soundhash-frontend" -- start
   pm2 startup
   pm2 save
   ```

3. **Configure Nginx**
   ```nginx
   # /etc/nginx/sites-available/soundhash
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

   ```bash
   sudo ln -s /etc/nginx/sites-available/soundhash /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

4. **SSL with Let's Encrypt**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

### Option 5: DigitalOcean App Platform

1. **Create App**
   - Go to DigitalOcean App Platform
   - Create new app from GitHub

2. **Configure**
   - Source: Your repository
   - Branch: main
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Run command: `npm start`

3. **Environment Variables**
   - Add in App Platform settings

## 🔒 SSL/TLS Setup

### Automatic (Vercel, Netlify, Amplify)
SSL certificates are automatically provisioned.

### Manual (EC2, VPS)
Use Let's Encrypt:

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## 🌍 CDN Configuration

### Cloudflare (Recommended)

1. **Add Site to Cloudflare**
   - Add your domain
   - Update nameservers

2. **Configure Settings**
   - SSL/TLS: Full (strict)
   - Always Use HTTPS: On
   - Auto Minify: HTML, CSS, JS
   - Brotli: On

3. **Page Rules**
   - Cache Everything for static assets
   - Edge Cache TTL: 1 month for static files

### AWS CloudFront

1. **Create Distribution**
   - Origin: Your Next.js deployment
   - Viewer Protocol Policy: Redirect HTTP to HTTPS
   - Compress Objects Automatically: Yes

2. **Cache Behaviors**
   - Static files: High TTL (31536000s)
   - API routes: No cache
   - HTML: Short TTL (3600s)

## 📊 Monitoring

### Vercel Analytics
- Automatically enabled
- Web Vitals tracking
- Real User Monitoring

### Custom Monitoring

```typescript
// app/layout.tsx
import { Analytics } from '@vercel/analytics/react'

export default function RootLayout() {
  return (
    <html>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  )
}
```

### Error Tracking (Sentry)

```bash
npm install @sentry/nextjs
```

```javascript
// sentry.client.config.js
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
});
```

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/frontend-deploy.yml
name: Frontend Deploy

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          
      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci
        
      - name: Build
        working-directory: ./frontend
        run: npm run build
        env:
          NEXT_PUBLIC_API_URL: ${{ secrets.API_URL }}
          
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          working-directory: ./frontend
```

## 🧪 Testing Before Deployment

```bash
# Build
npm run build

# Start production server locally
npm start

# Run Lighthouse audit
npx lighthouse http://localhost:3000 --view

# Check bundle size
npm run analyze
```

## 📝 Deployment Checklist

- [ ] Build succeeds without errors
- [ ] Environment variables set correctly
- [ ] CORS configured on backend
- [ ] API endpoints accessible
- [ ] SSL/TLS certificate active
- [ ] DNS records configured
- [ ] CDN configured (optional)
- [ ] Analytics set up
- [ ] Error tracking configured
- [ ] Monitoring alerts set up
- [ ] Backup strategy in place

## 🆘 Troubleshooting

### Build Failures
```bash
# Clear cache
rm -rf .next node_modules
npm install
npm run build
```

### Runtime Errors
- Check browser console
- Check server logs
- Verify API connectivity
- Check environment variables

### Performance Issues
- Enable compression
- Optimize images
- Use CDN
- Enable caching
- Monitor Web Vitals

## 🔗 Resources

- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [Vercel Documentation](https://vercel.com/docs)
- [Docker Documentation](https://docs.docker.com/)
- [AWS Amplify](https://aws.amazon.com/amplify/)
- [Netlify Docs](https://docs.netlify.com/)
