# Photography Portfolio Setup Guide

This is a modern photography portfolio website built with Flask (Python backend) and React (frontend).

## Features

- General feed of all photos
- Album organization based on folder structure
- Automatic EXIF metadata extraction
- Support for various aspect ratios (tall, wide, square, panoramic)
- Local development and CDN-ready for production
- Responsive design with lightbox view
- Photo navigation with keyboard shortcuts

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

## Project Structure

```
photography_portfolio/
├── backend/              # Flask API
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── photo_service.py
│   │   └── routes.py
│   ├── photos/          # Your photo storage folder
│   ├── requirements.txt
│   └── run.py
├── frontend/            # React SPA
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   └── App.jsx
│   └── package.json
└── README.md
```

## Backend Setup

### Option 1: Using UV (Recommended - Fast!)

1. Install UV if you haven't already:
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

   # Or with pip
   pip install uv
   ```

2. Navigate to the backend directory:
   ```bash
   cd backend
   ```

3. Install dependencies with UV:
   ```bash
   uv sync
   ```

4. Create a `.env` file (optional):
   ```bash
   cp .env.example .env
   ```

5. Add your photos to the `backend/photos/` directory:
   - Photos in the root will appear in "All Photos"
   - Create subfolders for albums (e.g., `photos/Vacation/`, `photos/Portraits/`)

6. Run the backend server:
   ```bash
   uv run python run.py
   ```

   The API will be available at `http://localhost:5001`

   Note: If port 5001 is in use, set a different port: `PORT=5002 uv run python run.py`

### Option 2: Using Traditional venv + pip

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file (optional):
   ```bash
   cp .env.example .env
   ```

5. Add your photos to the `backend/photos/` directory

6. Run the backend server:
   ```bash
   python run.py
   ```

   The API will be available at `http://localhost:5001`

   Note: If port 5001 is in use, set a different port: `PORT=5002 python run.py`

## Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

## Running Both Servers

You can run both servers simultaneously in different terminal windows:

**Terminal 1 (Backend with UV):**
```bash
cd backend
uv run python run.py
```

Or with traditional venv:
```bash
cd backend
source venv/bin/activate
python run.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

Then open your browser to `http://localhost:5173`

## Adding Photos

1. Place your photos in the `backend/photos/` directory
2. Organize them into subfolders for different albums
3. The app will automatically detect new photos and extract metadata
4. Refresh the page to see new photos

Example structure:
```
backend/photos/
├── Landscapes/
│   ├── sunset1.jpg
│   └── mountain.jpg
├── Portraits/
│   ├── person1.jpg
│   └── person2.jpg
└── standalone.jpg
```

## Production Deployment

### Backend

1. Update the `.env` file with production settings:
   ```
   USE_CDN=true
   CDN_BASE_URL=https://your-cdn.com
   PHOTOS_DIR=/path/to/photos
   ```

2. Deploy the Flask app using your preferred method (Gunicorn, uWSGI, etc.)

### Frontend

1. Build the frontend:
   ```bash
   cd frontend
   npm run build
   ```

2. Deploy the `dist/` folder to your hosting service

3. Update the API URL in production environment

## Configuration

### Backend Configuration (backend/app/config.py)

- `PHOTOS_DIR`: Directory where photos are stored
- `USE_CDN`: Whether to use CDN URLs for photos
- `CDN_BASE_URL`: Base URL for CDN
- `SUPPORTED_EXTENSIONS`: Supported image file types
- `THUMBNAIL_SIZE`: Size for thumbnail generation (optional)

### Frontend Configuration (frontend/.env)

- `VITE_API_URL`: Backend API URL (default: http://localhost:5000/api)

## Troubleshooting

**Photos not showing up:**
- Check that photos are in the correct directory
- Ensure file extensions are supported (.jpg, .jpeg, .png, .gif, .webp)
- Check backend console for errors

**CORS errors:**
- Ensure Flask-CORS is installed
- Check that the frontend URL is allowed in CORS configuration

**Metadata not displaying:**
- Some photos may not have EXIF data
- Try with photos from a camera that includes EXIF metadata

## License

MIT
