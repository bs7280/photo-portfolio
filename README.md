# Photography Portfolio Website

A modern, full-stack photography portfolio with Flask backend and React frontend.

## Features

- **General Feed**: Browse all your photos in a responsive masonry grid
- **Albums**: Automatic album organization based on folder structure
- **EXIF Metadata**: Automatically extracts camera settings, date, and other metadata
- **Mixed Aspect Ratios**: Supports tall, wide, square, and panoramic photos
- **Lightbox View**: Full-screen photo viewing with metadata display
- **Keyboard Navigation**: Navigate between photos using arrow keys
- **CDN Ready**: Works with local files in development, CDN in production

## Quick Start

See [SETUP.md](SETUP.md) for detailed setup instructions.

### Backend (Flask)

**With UV (recommended):**
```bash
cd backend
uv sync
uv run python run.py
# Server runs on http://localhost:5001
```

**Or with traditional venv:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
# Server runs on http://localhost:5001
```

### Frontend (React)
```bash
cd frontend
npm install
npm run dev
```

### Add Photos
Place your photos in `backend/photos/`:
- Root folder: Appears in "All Photos"
- Subfolders: Become albums (e.g., `photos/Vacation/` → "Vacation" album)

## Tech Stack

**Backend:**
- Flask - Web framework
- Pillow - Image processing and EXIF extraction
- Flask-CORS - Cross-origin requests

**Frontend:**
- React - UI framework
- Vite - Build tool
- React Router - Navigation
- Axios - API client

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment guides including:
- Render.com (easiest)
- Railway.app
- Vercel + Render
- Docker deployment
- Traditional VPS setup

## Project Structure

```
photography_portfolio/
├── backend/          # Flask API server
├── frontend/         # React SPA
├── README.md         # This file
├── SETUP.md          # Development setup guide
└── DEPLOYMENT.md     # Production deployment guide
```


