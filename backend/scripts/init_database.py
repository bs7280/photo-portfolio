#!/usr/bin/env python3
"""
Initialize the photo metadata database and sync with filesystem.

Usage:
    python scripts/init_database.py [--publish-all]

Options:
    --publish-all    Mark all existing photos as published (default: unpublished)
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import init_db, sync_photos_to_db, create_photo_metadata, get_db
from app.config import Config


def scan_photos_directory():
    """
    Scan the photos directory and return list of all photos.

    Returns:
        List of dicts with photo info (path, filename, album)
    """
    photos_dir = Path(Config.PHOTOS_DIR)

    if not photos_dir.exists():
        print(f"Error: Photos directory not found: {photos_dir}")
        return []

    photos = []
    for file_path in photos_dir.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in Config.SUPPORTED_EXTENSIONS:
            # Calculate relative path from photos directory
            rel_path = file_path.relative_to(photos_dir)

            # Determine album (parent folder name, or None if in root)
            if len(rel_path.parts) > 1:
                album = rel_path.parts[0]
            else:
                album = None

            photos.append({
                'path': str(rel_path),
                'filename': file_path.name,
                'album': album
            })

    return photos


def initialize_database(publish_all: bool = False):
    """
    Initialize database and populate with photos from filesystem.

    Args:
        publish_all: If True, mark all photos as published
    """
    print("Initializing photo metadata database...")
    print(f"Database path: {Config.DATABASE_PATH}")
    print(f"Photos directory: {Config.PHOTOS_DIR}")
    print()

    # Create database and tables
    from app import create_app
    app = create_app()

    with app.app_context():
        init_db()
        print("Database tables created successfully.")
        print()

        # Scan photos directory
        print("Scanning photos directory...")
        photos = scan_photos_directory()
        print(f"Found {len(photos)} photos.")
        print()

        if not photos:
            print("No photos found. Database initialized but empty.")
            return

        # Sync photos to database
        print("Syncing photos to database...")
        result = sync_photos_to_db(photos)
        print(f"Added {result['added']} new photos to database.")
        print(f"Removed {result['removed']} orphaned records.")
        print()

        # Optionally publish all photos
        if publish_all:
            print("Publishing all photos...")
            db = get_db()
            cursor = db.execute('UPDATE photos SET published = 1')
            db.commit()
            print(f"Published {cursor.rowcount} photos.")
            print()

        # Show summary
        db = get_db()
        total_photos = db.execute('SELECT COUNT(*) FROM photos').fetchone()[0]
        published_count = db.execute('SELECT COUNT(*) FROM photos WHERE published = 1').fetchone()[0]
        unpublished_count = total_photos - published_count

        print("Database initialization complete!")
        print()
        print("Summary:")
        print(f"  Total photos: {total_photos}")
        print(f"  Published: {published_count}")
        print(f"  Unpublished: {unpublished_count}")
        print()

        # Show albums
        albums = db.execute('SELECT DISTINCT album FROM photos WHERE album IS NOT NULL ORDER BY album').fetchall()
        if albums:
            print(f"Albums found: {len(albums)}")
            for album in albums:
                count = db.execute('SELECT COUNT(*) FROM photos WHERE album = ?', (album['album'],)).fetchone()[0]
                print(f"  - {album['album']}: {count} photos")
        else:
            print("No albums found (all photos in root directory).")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Initialize photo metadata database and sync with filesystem.'
    )
    parser.add_argument(
        '--publish-all',
        action='store_true',
        help='Mark all existing photos as published (default: unpublished)'
    )

    args = parser.parse_args()

    try:
        initialize_database(publish_all=args.publish_all)
    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
