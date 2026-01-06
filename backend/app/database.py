"""
Database layer for photo metadata storage using SQLite.
"""
import sqlite3
import json
import os
from pathlib import Path
from typing import Optional, Dict, List, Any
from flask import g
from .config import Config
import boto3


def get_db() -> sqlite3.Connection:
    """
    Get database connection. Creates connection if it doesn't exist in Flask's g object.
    Uses row factory to return dict-like rows.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            Config.DATABASE_PATH,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    """
    Close database connection if it exists.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """
    Initialize database with schema. Creates tables if they don't exist.
    """
    db = get_db()

    # Create photos table
    db.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            album TEXT,
            published INTEGER DEFAULT 0,
            custom_title TEXT,
            description TEXT,
            tags TEXT,
            notes TEXT,
            exif_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migration: Add exif_data column if it doesn't exist
    try:
        db.execute('SELECT exif_data FROM photos LIMIT 1')
    except sqlite3.OperationalError:
        print("Adding exif_data column to photos table...")
        db.execute('ALTER TABLE photos ADD COLUMN exif_data TEXT')
        db.commit()

    # Create indexes for photos
    db.execute('CREATE INDEX IF NOT EXISTS idx_path ON photos(path)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_published ON photos(published)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_album ON photos(album)')

    # Create albums table
    db.execute('''
        CREATE TABLE IF NOT EXISTS albums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            display_name TEXT,
            description TEXT,
            cover_photo_path TEXT,
            sort_order INTEGER DEFAULT 0,
            published INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create index for albums
    db.execute('CREATE INDEX IF NOT EXISTS idx_album_name ON albums(name)')

    db.commit()


# Photo CRUD operations

def get_photo_metadata(path: str) -> Optional[Dict[str, Any]]:
    """
    Get custom metadata for a photo by path.

    Args:
        path: Relative path to photo from PHOTOS_DIR

    Returns:
        Dict with photo metadata or None if not found
    """
    db = get_db()
    row = db.execute(
        'SELECT * FROM photos WHERE path = ?',
        (path,)
    ).fetchone()

    if row is None:
        return None

    result = dict(row)
    # Parse tags JSON string to list
    if result.get('tags'):
        try:
            result['tags'] = json.loads(result['tags'])
        except json.JSONDecodeError:
            result['tags'] = []
    else:
        result['tags'] = []

    # Parse exif_data JSON string to dict
    if result.get('exif_data'):
        try:
            result['exif_data'] = json.loads(result['exif_data'])
        except json.JSONDecodeError:
            result['exif_data'] = {}
    else:
        result['exif_data'] = {}

    # Convert published to boolean
    result['published'] = bool(result['published'])

    return result


def get_all_photo_metadata() -> List[Dict[str, Any]]:
    """
    Get all photo metadata records.

    Returns:
        List of photo metadata dicts
    """
    db = get_db()
    rows = db.execute('SELECT * FROM photos').fetchall()

    results = []
    for row in rows:
        result = dict(row)
        # Parse tags JSON
        if result.get('tags'):
            try:
                result['tags'] = json.loads(result['tags'])
            except json.JSONDecodeError:
                result['tags'] = []
        else:
            result['tags'] = []

        # Convert published to boolean
        result['published'] = bool(result['published'])
        results.append(result)

    return results


def create_photo_metadata(path: str, filename: str, album: str = None, published: bool = False, exif_data: Dict = None) -> int:
    """
    Create metadata record for a new photo.

    Args:
        path: Relative path to photo
        filename: Photo filename
        album: Album name (optional)
        published: Published flag (default False)
        exif_data: EXIF metadata dict (optional)

    Returns:
        ID of created record
    """
    db = get_db()
    exif_json = json.dumps(exif_data) if exif_data else None
    cursor = db.execute(
        '''
        INSERT INTO photos (path, filename, album, published, exif_data)
        VALUES (?, ?, ?, ?, ?)
        ''',
        (path, filename, album, 1 if published else 0, exif_json)
    )
    db.commit()
    return cursor.lastrowid


def update_photo_metadata(path: str, metadata: Dict[str, Any]) -> bool:
    """
    Update custom metadata for a photo.

    Args:
        path: Relative path to photo
        metadata: Dict with fields to update (published, custom_title, description, tags, notes)

    Returns:
        True if updated, False if photo not found
    """
    db = get_db()

    # Build UPDATE query dynamically based on provided fields
    allowed_fields = ['published', 'custom_title', 'description', 'tags', 'notes', 'album', 'filename']
    updates = []
    values = []

    for field in allowed_fields:
        if field in metadata:
            updates.append(f'{field} = ?')
            # Handle tags as JSON
            if field == 'tags':
                values.append(json.dumps(metadata[field]) if metadata[field] else None)
            # Handle published as integer
            elif field == 'published':
                values.append(1 if metadata[field] else 0)
            else:
                values.append(metadata[field])

    if not updates:
        return False

    # Always update updated_at
    updates.append('updated_at = CURRENT_TIMESTAMP')

    query = f"UPDATE photos SET {', '.join(updates)} WHERE path = ?"
    values.append(path)

    cursor = db.execute(query, values)
    db.commit()

    return cursor.rowcount > 0


def delete_photo_metadata(path: str) -> bool:
    """
    Delete metadata record for a photo.

    Args:
        path: Relative path to photo

    Returns:
        True if deleted, False if not found
    """
    db = get_db()
    cursor = db.execute('DELETE FROM photos WHERE path = ?', (path,))
    db.commit()
    return cursor.rowcount > 0


def get_published_photo_paths() -> List[str]:
    """
    Get list of paths for all published photos.

    Returns:
        List of photo paths
    """
    db = get_db()
    rows = db.execute('SELECT path FROM photos WHERE published = 1').fetchall()
    return [row['path'] for row in rows]


def sync_photos_to_db(photos_list: List[Dict[str, str]]) -> Dict[str, int]:
    """
    Sync filesystem photos with database. Creates missing records, removes orphaned records.

    Args:
        photos_list: List of photo dicts with 'path', 'filename', 'album', optionally 'exif_data' keys

    Returns:
        Dict with 'added' and 'removed' counts
    """
    db = get_db()

    # Get existing paths from DB
    existing_paths = set(
        row['path'] for row in db.execute('SELECT path FROM photos').fetchall()
    )

    # Get current paths from filesystem
    current_paths = set(photo['path'] for photo in photos_list)

    # Add missing photos
    added = 0
    for photo in photos_list:
        if photo['path'] not in existing_paths:
            create_photo_metadata(
                path=photo['path'],
                filename=photo['filename'],
                album=photo.get('album'),
                published=False,
                exif_data=photo.get('exif_data')
            )
            added += 1

    # Remove orphaned records
    removed = 0
    orphaned_paths = existing_paths - current_paths
    for path in orphaned_paths:
        delete_photo_metadata(path)
        removed += 1

    return {'added': added, 'removed': removed}


# Album CRUD operations

def get_album_metadata(name: str) -> Optional[Dict[str, Any]]:
    """
    Get metadata for an album by name.

    Args:
        name: Album name (folder name)

    Returns:
        Dict with album metadata or None if not found
    """
    db = get_db()
    row = db.execute(
        'SELECT * FROM albums WHERE name = ?',
        (name,)
    ).fetchone()

    if row is None:
        return None

    result = dict(row)
    result['published'] = bool(result['published'])
    return result


def get_all_album_metadata() -> List[Dict[str, Any]]:
    """
    Get all album metadata records.

    Returns:
        List of album metadata dicts
    """
    db = get_db()
    rows = db.execute('SELECT * FROM albums ORDER BY sort_order, name').fetchall()

    results = []
    for row in rows:
        result = dict(row)
        result['published'] = bool(result['published'])
        results.append(result)

    return results


def create_album_metadata(name: str, display_name: str = None, published: bool = True) -> int:
    """
    Create metadata record for a new album.

    Args:
        name: Album name (folder name)
        display_name: Custom display name (optional)
        published: Published flag (default True)

    Returns:
        ID of created record
    """
    db = get_db()
    cursor = db.execute(
        '''
        INSERT INTO albums (name, display_name, published)
        VALUES (?, ?, ?)
        ''',
        (name, display_name, 1 if published else 0)
    )
    db.commit()
    return cursor.lastrowid


def update_album_metadata(name: str, metadata: Dict[str, Any]) -> bool:
    """
    Update metadata for an album.

    Args:
        name: Album name (folder name)
        metadata: Dict with fields to update

    Returns:
        True if updated, False if album not found
    """
    db = get_db()

    allowed_fields = ['display_name', 'description', 'cover_photo_path', 'sort_order', 'published']
    updates = []
    values = []

    for field in allowed_fields:
        if field in metadata:
            updates.append(f'{field} = ?')
            if field == 'published':
                values.append(1 if metadata[field] else 0)
            else:
                values.append(metadata[field])

    if not updates:
        return False

    updates.append('updated_at = CURRENT_TIMESTAMP')

    query = f"UPDATE albums SET {', '.join(updates)} WHERE name = ?"
    values.append(name)

    cursor = db.execute(query, values)
    db.commit()

    return cursor.rowcount > 0


def delete_album_metadata(name: str) -> bool:
    """
    Delete metadata record for an album.

    Args:
        name: Album name (folder name)

    Returns:
        True if deleted, False if not found
    """
    db = get_db()
    cursor = db.execute('DELETE FROM albums WHERE name = ?', (name,))
    db.commit()
    return cursor.rowcount > 0


def download_published_db_from_r2() -> bool:
    """
    Download the published photos database from R2.
    This is used on fly.io startup to get the latest published photo metadata
    without having to list all R2 objects.

    Returns:
        True if successful, False otherwise
    """
    if not Config.USE_CDN:
        print("Not using CDN, skipping database download from R2")
        return False

    if not Config.R2_ACCESS_KEY_ID:
        print("R2 credentials not configured, skipping database download")
        return False

    try:
        print("Downloading published database from R2...")

        # Create S3 client
        s3_client = boto3.client(
            's3',
            endpoint_url=Config.R2_ENDPOINT_URL,
            aws_access_key_id=Config.R2_ACCESS_KEY_ID,
            aws_secret_access_key=Config.R2_SECRET_ACCESS_KEY,
            region_name='auto'
        )

        # Download database file
        db_path = Config.DATABASE_PATH

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        s3_client.download_file(
            Config.R2_BUCKET_NAME,
            'metadata/published.db',
            db_path
        )

        print(f"✓ Published database downloaded to {db_path}")
        return True

    except Exception as e:
        # Handle 404 (database doesn't exist yet - normal on first deploy)
        error_msg = str(e)
        if '404' in error_msg or 'Not Found' in error_msg or 'NoSuchKey' in error_msg:
            print("Published database not found in R2 (this is normal before first sync)")
            print("App will start with empty photo list until you sync from admin")
        else:
            print(f"Error downloading published database from R2: {e}")
            import traceback
            traceback.print_exc()
        return False
