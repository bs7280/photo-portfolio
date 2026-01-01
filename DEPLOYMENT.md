# Deployment Guide

## Option 1: Render.com (Recommended - Easiest)

Render offers free hosting for both frontend and backend with automatic HTTPS.

### Prerequisites
- GitHub account
- Render.com account (free)
- Push your code to GitHub

### Step 1: Prepare Your Backend for Production

1. Create a production requirements file if needed (optional):
   ```bash
   cd backend
   echo "gunicorn>=21.0.0" >> requirements.txt
   ```

2. The backend is already configured to read the PORT from environment variables.

### Step 2: Deploy Backend to Render

1. Go to [Render.com](https://render.com) and sign in
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `photography-portfolio-api`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app`
   - **Instance Type**: Free

5. Add Environment Variables:
   - `PHOTOS_DIR`: `/opt/render/project/src/backend/photos`
   - `USE_CDN`: `false` (or `true` if using CDN)
   - `BACKEND_URL`: (leave empty, will be auto-set)
   - `PORT`: (Render sets this automatically)

6. Click "Create Web Service"

7. Once deployed, copy the service URL (e.g., `https://photography-portfolio-api.onrender.com`)

### Step 3: Deploy Frontend to Render

1. Create a build script in `frontend/package.json` if not present:
   ```json
   "scripts": {
     "build": "vite build",
     "preview": "vite preview"
   }
   ```

2. In Render dashboard, click "New +" → "Static Site"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `photography-portfolio`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`

5. Add Environment Variable:
   - `VITE_API_URL`: `https://photography-portfolio-api.onrender.com/api` (use your backend URL from Step 2)

6. Click "Create Static Site"

### Step 4: Upload Photos

You have two options for photos:

**Option A: Include in Repository (Simple)**
- Add photos to `backend/photos/` directory
- Commit and push to GitHub
- Render will deploy with photos included
- Note: Not ideal for large photo collections or frequent updates

**Option B: Use Cloud Storage (Recommended for Production)**
- Use a CDN like Cloudflare R2, AWS S3, or Backblaze B2
- Upload photos to your CDN
- Update backend environment variables:
  - `USE_CDN`: `true`
  - `CDN_BASE_URL`: Your CDN URL

### Limitations of Free Tier
- Backend spins down after 15 minutes of inactivity (first request after sleep takes ~30 seconds)
- 750 hours/month free (enough for hobby projects)

---

## Option 2: Railway.app (Similar to Render)

Railway is another great option with generous free tier.

### Deploy Backend
1. Go to [Railway.app](https://railway.app)
2. "New Project" → "Deploy from GitHub"
3. Select your repository
4. Railway auto-detects Python
5. Set root directory to `backend`
6. Add environment variables (same as Render)
7. Deploy!

### Deploy Frontend
1. "New Project" → "Deploy from GitHub"
2. Select repository
3. Set build command: `cd frontend && npm install && npm run build`
4. Set start command: `npm run preview` or use static serving
5. Add `VITE_API_URL` environment variable

---

## Option 3: Vercel (Frontend) + Render/Railway (Backend)

### Backend: Deploy to Render or Railway (see above)

### Frontend: Deploy to Vercel
1. Go to [Vercel.com](https://vercel.com)
2. Import your GitHub repository
3. Framework Preset: Vite
4. Root Directory: `frontend`
5. Environment Variables:
   - `VITE_API_URL`: Your backend URL
6. Deploy!

---

## Option 4: Docker + Any VPS (DigitalOcean, Linode, etc.)

If you want more control, use Docker.

### Step 1: Create Dockerfiles

Backend Dockerfile already exists, create frontend Dockerfile:

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
RUN npm install -g serve
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
```

### Step 2: Create docker-compose.yml

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "5001:5001"
    environment:
      - PORT=5001
      - PHOTOS_DIR=/app/photos
      - USE_CDN=false
      - BACKEND_URL=http://localhost:5001
    volumes:
      - ./backend/photos:/app/photos

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://your-server-ip:5001/api
    depends_on:
      - backend
```

### Step 3: Deploy to VPS
1. SSH into your VPS
2. Install Docker and Docker Compose
3. Clone your repository
4. Run `docker-compose up -d`
5. Set up nginx as reverse proxy (optional but recommended)

---

## Option 5: Single Server with Nginx (Traditional)

For maximum control on a VPS:

1. Set up a Ubuntu/Debian server
2. Install Python, Node.js, and Nginx
3. Run backend with gunicorn/systemd
4. Build frontend and serve with nginx
5. Configure nginx as reverse proxy

This requires more setup but gives you full control.

---

## Recommended Approach for You

**For easiest deployment:**
1. **Render.com** - Deploy both frontend and backend in ~10 minutes
2. **Railway.app** - Similar ease, slightly different interface
3. **Vercel (frontend) + Render (backend)** - Best performance for frontend

**For production with many photos:**
- Use a CDN (Cloudflare R2, Backblaze B2)
- Deploy backend to Render/Railway
- Deploy frontend to Vercel/Netlify

## Photo Storage Recommendations

**Small Collection (<100 photos, <500MB):**
- Include in repository
- Deploy to Render/Railway

**Medium Collection (<1000 photos, <5GB):**
- Cloudflare R2 (10GB free)
- Backblaze B2 (10GB free)

**Large Collection:**
- AWS S3 + CloudFront
- Cloudflare R2 with custom domain

---

## Next Steps

1. Choose your deployment platform
2. Push code to GitHub if you haven't
3. Follow the relevant guide above
4. Update environment variables
5. Deploy!

Need help with any specific deployment option? Let me know!
