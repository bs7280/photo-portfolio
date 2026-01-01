# Photography Portfolio Backend

Flask-based REST API for serving photography portfolio data.

## Setup with UV

UV is a fast Python package manager. Install it first:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

Then set up the project:

```bash
# Install dependencies
uv sync

# Run the server
uv run python run.py
```

## Alternative: Traditional Setup

If you prefer using venv and pip:

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

## API Endpoints

- `GET /api/photos` - Get all photos
- `GET /api/albums` - Get all albums
- `GET /api/albums/:id/photos` - Get photos in an album
- `GET /api/photos/:path` - Serve a photo file (local dev only)
- `GET /api/thumbnails/:path` - Serve a thumbnail (local dev only)
- `GET /api/health` - Health check

## Configuration

Create a `.env` file (see `.env.example`) to configure:

- `PHOTOS_DIR` - Directory where photos are stored
- `USE_CDN` - Whether to use CDN for photos (true/false)
- `CDN_BASE_URL` - Base URL for CDN

## Photo Organization

Photos should be organized in the `photos/` directory:

```
photos/
├── album1/
│   ├── photo1.jpg
│   └── photo2.jpg
├── album2/
│   └── photo3.jpg
└── standalone.jpg
```

- Subfolders become albums
- Photos in subfolders appear in both "All Photos" and their album
- Photos in the root only appear in "All Photos"
