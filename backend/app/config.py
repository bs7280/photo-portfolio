import os
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    PHOTOS_DIR = os.getenv('PHOTOS_DIR', str(BASE_DIR / 'photos'))
    USE_CDN = os.getenv('USE_CDN', 'false').lower() == 'true'
    CDN_BASE_URL = os.getenv('CDN_BASE_URL', '')

    # Backend URL for local development (used when not using CDN)
    BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5001')

    # Edit mode flag - enables write operations (create/update/delete)
    EDIT_MODE = os.getenv('EDIT_MODE', 'false').lower() == 'true'

    # Database path for photo metadata
    DATABASE_PATH = os.getenv('DATABASE_PATH', str(BASE_DIR / 'photos_metadata.db'))

    # R2 Configuration
    R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID', '')
    R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY', '')
    R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME', '')
    R2_ENDPOINT_URL = os.getenv('R2_ENDPOINT_URL', '')

    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    THUMBNAIL_SIZE = (400, 400)
    MAX_IMAGE_SIZE = (2000, 2000)
