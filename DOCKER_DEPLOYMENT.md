# Docker Deployment Guide

This guide explains how to deploy the photography portfolio using Docker and GitHub Container Registry (GHCR).

## Overview

The application consists of two Docker images:
- **Backend**: Flask API with photo management and R2 sync
- **Frontend**: React SPA served by Nginx

Images are automatically built and pushed to GHCR on push to main branch.

## Prerequisites

1. **GitHub account** with a repository
2. **Docker** and **Docker Compose** installed on your server
3. **Cloudflare R2** bucket configured
4. **Your photos** organized locally for initial sync

## Setup Instructions

### 1. Configure GitHub Container Registry

The GitHub Actions workflow will automatically build and push images to GHCR when you push to the main branch.

Make sure your repository is public OR you have access to GitHub Packages.

### 2. Initial Local Setup (Edit Mode)

On your local machine with edit capabilities:

```bash
# Clone the repository
git clone https://github.com/your-username/photography-portfolio.git
cd photography-portfolio

# Copy environment file
cp .env.example .env

# Edit .env with your R2 credentials
nano .env

# Start services in edit mode
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:5001
```

### 3. Populate Database with EXIF Data

```bash
# In the UI, click "Sync Database" button
# This will scan all photos and extract EXIF metadata

# Or via API:
curl -X POST http://localhost:5001/api/sync
```

### 4. Publish Photos and Deploy to R2

```bash
# 1. In the UI, select photos and click "Publish"
# 2. Click "Deploy to R2" button to upload to Cloudflare
# 3. This uploads photos, thumbnails, and syncs R2 bucket
```

### 5. Copy Database for Production

The production deployment needs the database with EXIF data:

```bash
# Copy your local database
cp backend/photos_metadata.db backend/photos_metadata_prod.db

# Or via SSH to your server:
scp backend/photos_metadata.db user@server:/path/to/production/data/
```

### 6. Deploy to Production Server

On your home server:

```bash
# Create deployment directory
mkdir -p ~/photography-portfolio
cd ~/photography-portfolio

# Copy docker-compose.prod.yml and .env
# (Download from repo or copy via scp)

# Create .env file with production settings
cat > .env << 'ENVEOF'
GITHUB_USERNAME=your-github-username
BACKEND_URL=http://your-server-ip:5001
CDN_BASE_URL=https://your-bucket.r2.dev
R2_ENDPOINT_URL=https://account-id.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your-key
R2_SECRET_ACCESS_KEY=your-secret
R2_BUCKET_NAME=your-bucket
ENVEOF

# Pull images from GHCR
docker-compose -f docker-compose.prod.yml pull

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 7. Copy Database to Production

```bash
# On your server, copy the database to the Docker volume
docker cp photos_metadata.db photography-portfolio-backend-1:/app/photos_metadata.db

# Or mount it as a volume in docker-compose.prod.yml
```

## Environment Modes

### Edit Mode (Local - docker-compose.yml)
- `EDIT_MODE=true`
- `USE_CDN=false`
- Volumes: photos, database, thumbnails
- Features: Create/edit/delete photos, sync database, deploy to R2

### Production Mode (Server - docker-compose.prod.yml)
- `EDIT_MODE=false`
- `USE_CDN=true`
- Volume: database only (EXIF data)
- Features: View published photos from R2 (read-only)

## Updating the Application

### Update Code

```bash
# On local machine
git pull origin main

# Push triggers GitHub Actions to build new images

# On production server
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Update Photos

```bash
# On local machine (edit mode)
1. Copy new photos to backend/photos/
2. Click "Sync Database" to add new photos
3. Select and publish new photos
4. Click "Deploy to R2" to sync
5. Copy updated database to production server
```

## Volumes and Data Persistence

### Local (Edit Mode)
```
backend/photos          -> Container /app/photos
backend/thumbnails      -> Container /app/thumbnails
backend/photos_metadata.db -> Container /app/photos_metadata.db
```

### Production (Read-Only Mode)
```
database volume         -> Container /app/data (database only)
Photos served from R2 (no local storage needed)
```

## Troubleshooting

### Images not showing in production
- Verify CDN_BASE_URL is correct
- Check R2 bucket is public or has proper CORS
- Ensure photos were deployed to R2

### EXIF data missing
- Run "Sync Database" in edit mode
- Copy updated database to production
- Restart backend container

### Permission issues
- Check volume mount permissions
- Ensure Docker has access to mounted directories

## GitHub Actions Workflow

The workflow (`.github/workflows/docker-build.yml`) automatically:
- Builds images on push to main
- Tags with branch name, commit SHA, and "latest"
- Pushes to GHCR
- Supports multi-platform builds (amd64, arm64)

Workflow triggers:
- Push to main/master
- Git tags (v*)
- Manual dispatch

## Security Notes

- Keep R2 credentials in `.env` file (not committed)
- Use read-only R2 credentials for production if possible
- GHCR images can be private (requires authentication to pull)
- Edit mode should only run locally, not exposed to internet
