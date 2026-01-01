# Fly.io Deployment Guide

## Prerequisites

1. Install Fly.io CLI:
   ```bash
   # macOS
   brew install flyctl

   # Or use the install script
   curl -L https://fly.io/install.sh | sh
   ```

2. Login to Fly.io:
   ```bash
   flyctl auth login
   ```

## Backend Deployment

### Step 1: Launch the App

```bash
cd backend
flyctl launch
```

**Answer the prompts:**
- Choose app name: `photography-portfolio` (or whatever you prefer)
- Choose region: Select one close to you (or `sjc` for San Jose)
- Would you like to set up a Postgresql database? **No**
- Would you like to set up an Upstash Redis database? **No**
- Would you like to deploy now? **No** (we need to set secrets first)

### Step 2: Set Environment Secrets

Set your R2 credentials as secrets (these won't be visible in fly.toml):

```bash
flyctl secrets set \
  CDN_BASE_URL=https://pub-d96aa4427c6e4947a839e415709d9af2.r2.dev \
  R2_ACCOUNT_ID=4e1c7b56bf43accc4b8ac8f46304c300 \
  R2_ACCESS_KEY_ID=your-access-key-id \
  R2_SECRET_ACCESS_KEY=your-secret-access-key \
  R2_BUCKET_NAME=photography-portfolio \
  R2_ENDPOINT_URL=https://4e1c7b56bf43accc4b8ac8f46304c300.r2.cloudflarestorage.com
```

**Important:** Replace the R2 credentials with your actual values from `.env`

### Step 3: Deploy

```bash
flyctl deploy
```

This will:
- Build your Docker image
- Push it to Fly.io
- Deploy your app
- Give you a URL like `https://photography-portfolio.fly.dev`

### Step 4: Set BACKEND_URL

After deployment, set the backend URL to your Fly.io app URL:

```bash
flyctl secrets set BACKEND_URL=https://your-app-name.fly.dev
```

### Step 5: Test

Visit your app URL to test the API:
```bash
flyctl open
# Or manually visit: https://your-app-name.fly.dev/api/health
```

## Frontend Deployment (Vercel - Recommended)

### Step 1: Push to GitHub

Make sure your code is pushed to GitHub:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo-url>
git push -u origin main
```

### Step 2: Deploy to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click "New Project"
3. Import your repository
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `dist` (default)

5. Add Environment Variable:
   - **Name**: `VITE_API_URL`
   - **Value**: `https://your-fly-app-name.fly.dev/api`

6. Click "Deploy"

Vercel will give you a URL like `https://photography-portfolio.vercel.app`

## Fly.io Useful Commands

```bash
# View logs
flyctl logs

# Check app status
flyctl status

# SSH into your app
flyctl ssh console

# Scale your app
flyctl scale count 1  # Keep 1 instance running always
flyctl scale count 0  # Scale to 0 when idle (free tier)

# Update secrets
flyctl secrets set KEY=value

# View secrets (names only, not values)
flyctl secrets list

# Restart your app
flyctl apps restart photography-portfolio
```

## Cost Optimization

Fly.io free tier includes:
- Up to 3 shared-cpu-1x VMs with 256MB RAM
- 160GB outbound data transfer

Your current config uses:
- `auto_stop_machines = true` - Stops when idle
- `auto_start_machines = true` - Starts on first request
- `min_machines_running = 0` - No always-on machines (free tier friendly)

This means:
- App stops after ~5 minutes of inactivity
- First request after sleeping takes ~2-3 seconds to wake up
- Subsequent requests are fast
- **Perfect for portfolio sites with occasional traffic**

If you want always-on (faster cold starts):
```bash
flyctl scale count 1
```

## Updating Your App

When you make changes:

```bash
cd backend
flyctl deploy
```

## Troubleshooting

**App won't start:**
```bash
flyctl logs
```

**Check if secrets are set:**
```bash
flyctl secrets list
```

**Test locally with same environment:**
```bash
flyctl secrets list  # Note which secrets exist
# Set them in local .env for testing
```

## Next Steps

After deployment:
1. Test your backend: `https://your-app.fly.dev/api/health`
2. Test photos endpoint: `https://your-app.fly.dev/api/photos`
3. Update frontend on Vercel with correct backend URL
4. Visit your Vercel URL and enjoy your deployed portfolio!
