"""
Service for syncing published photos to Cloudflare R2 bucket.
"""
from pathlib import Path
from typing import Dict, List, Set
from app.config import Config
from app.database import get_db
from app.thumbnail_service import ThumbnailService
import boto3
import sqlite3
import tempfile


class SyncService:
    def __init__(self):
        self.photos_dir = Path(Config.PHOTOS_DIR).resolve()
        self.thumbnail_service = ThumbnailService()

        # Initialize R2 client
        if Config.R2_ACCESS_KEY_ID:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=Config.R2_ENDPOINT_URL,
                aws_access_key_id=Config.R2_ACCESS_KEY_ID,
                aws_secret_access_key=Config.R2_SECRET_ACCESS_KEY,
                region_name='auto'
            )
            self.bucket_name = Config.R2_BUCKET_NAME
        else:
            self.s3_client = None
            self.bucket_name = None

    def get_published_photos(self) -> List[str]:
        """
        Get list of all published photo paths from database.

        Returns:
            List of relative paths for published photos
        """
        db = get_db()
        cursor = db.execute('SELECT path FROM photos WHERE published = 1')
        return [row['path'] for row in cursor.fetchall()]

    def list_r2_objects(self) -> Set[str]:
        """
        List all objects currently in R2 bucket (excluding thumbnails).

        Returns:
            Set of object keys (paths)
        """
        if not self.s3_client:
            return set()

        try:
            objects = set()
            paginator = self.s3_client.get_paginator('list_objects_v2')

            for page in paginator.paginate(Bucket=self.bucket_name):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        # Skip thumbnails directory
                        if not key.startswith('thumbnails/'):
                            objects.add(key)

            return objects
        except Exception as e:
            print(f"Error listing R2 objects: {e}")
            return set()

    def sync_to_r2(self) -> Dict:
        """
        Sync published photos to R2 bucket.

        Compares local published photos with R2 objects and:
        - Uploads new/missing published photos
        - Deletes unpublished/removed photos from R2

        Returns:
            Dict with sync results: uploaded, deleted, errors
        """
        if not self.s3_client:
            return {
                'success': False,
                'error': 'R2 credentials not configured',
                'uploaded': 0,
                'deleted': 0,
                'errors': []
            }

        result = {
            'success': True,
            'uploaded': 0,
            'deleted': 0,
            'errors': [],
            'warnings': [],
            'uploaded_files': [],
            'deleted_files': [],
            'thumbnails_generated': 0,
            'database_exported': False
        }

        try:
            # Get published photos from database
            published_paths = set(self.get_published_photos())
            print(f"Found {len(published_paths)} published photos")

            # Ensure all published photos have thumbnails before deploying
            print("Checking and generating missing thumbnails...")
            for photo_path in published_paths:
                thumbnail_path = self.thumbnail_service.get_thumbnail_path(photo_path)
                if not thumbnail_path.exists():
                    generated = self.thumbnail_service.generate_thumbnail(photo_path)
                    if generated:
                        result['thumbnails_generated'] += 1
                        print(f"Generated thumbnail for: {photo_path}")
                    else:
                        # Treat as warning, not error (photo file might be missing)
                        warning_msg = f"Skipping {photo_path} - source file not found"
                        result['warnings'].append(warning_msg)
                        print(f"Warning: {warning_msg}")

            if result['thumbnails_generated'] > 0:
                print(f"Generated {result['thumbnails_generated']} missing thumbnails")

            # Get current R2 objects
            r2_objects = self.list_r2_objects()
            print(f"Found {len(r2_objects)} objects in R2")

            # Filter out photos that don't exist on disk
            valid_published_paths = set()
            for path in published_paths:
                local_file = self.photos_dir / path
                if local_file.exists():
                    valid_published_paths.add(path)
                else:
                    warning_msg = f"Skipping {path} - marked as published but file not found"
                    if warning_msg not in result['warnings']:
                        result['warnings'].append(warning_msg)
                        print(f"Warning: {warning_msg}")

            # Determine what to upload (published but not in R2)
            to_upload = valid_published_paths - r2_objects
            print(f"Need to upload {len(to_upload)} files")

            # Determine what to delete (in R2 but not published or not existing)
            to_delete = r2_objects - valid_published_paths
            print(f"Need to delete {len(to_delete)} files")

            # Upload new/missing files
            for path in to_upload:
                try:
                    local_file = self.photos_dir / path
                    if not local_file.exists():
                        result['errors'].append(f"Local file not found: {path}")
                        continue

                    content_type = self._get_content_type(path)

                    # Upload main photo to R2
                    self.s3_client.upload_file(
                        str(local_file),
                        self.bucket_name,
                        path,
                        ExtraArgs={'ContentType': content_type}
                    )

                    # Generate thumbnail (if not exists) and upload to R2
                    thumbnail_file = self.thumbnail_service.generate_thumbnail(path)
                    if thumbnail_file and thumbnail_file.exists():
                        thumbnail_r2_path = f"thumbnails/{path}"
                        self.s3_client.upload_file(
                            str(thumbnail_file),
                            self.bucket_name,
                            thumbnail_r2_path,
                            ExtraArgs={'ContentType': 'image/jpeg'}  # Thumbnails are always JPEG
                        )
                        print(f"Uploaded: {path} (with generated thumbnail)")
                    else:
                        print(f"Warning: Failed to generate thumbnail for {path}, skipping thumbnail upload")

                    result['uploaded'] += 1
                    result['uploaded_files'].append(path)

                except Exception as e:
                    error_msg = f"Failed to upload {path}: {str(e)}"
                    result['errors'].append(error_msg)
                    print(error_msg)

            # Delete unpublished/removed files from R2
            for path in to_delete:
                try:
                    # Delete main photo
                    self.s3_client.delete_object(
                        Bucket=self.bucket_name,
                        Key=path
                    )

                    # Delete corresponding thumbnail
                    thumbnail_path = f"thumbnails/{path}"
                    try:
                        self.s3_client.delete_object(
                            Bucket=self.bucket_name,
                            Key=thumbnail_path
                        )
                    except Exception:
                        # Thumbnail might not exist, that's okay
                        pass

                    result['deleted'] += 1
                    result['deleted_files'].append(path)
                    print(f"Deleted from R2: {path} (with thumbnail)")

                except Exception as e:
                    error_msg = f"Failed to delete {path}: {str(e)}"
                    result['errors'].append(error_msg)
                    print(error_msg)

            # Also handle thumbnails directory cleanup
            self._sync_thumbnails(valid_published_paths)

            # Export and upload published database
            print("Exporting published photos database...")
            db_upload_success = self._export_and_upload_published_db()
            result['database_exported'] = db_upload_success
            if db_upload_success:
                print("✓ Published database uploaded to R2")
            else:
                result['warnings'].append("Failed to upload published database")

            if result['errors']:
                result['success'] = False

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            print(f"Sync error: {e}")
            import traceback
            traceback.print_exc()

        return result

    def _sync_thumbnails(self, published_paths: Set[str]):
        """
        Sync thumbnails directory - delete thumbnails for unpublished photos.
        """
        try:
            # List all thumbnails
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix='thumbnails/'):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        # Extract photo path from thumbnail path
                        photo_path = key.replace('thumbnails/', '', 1)

                        # Delete if photo is not published
                        if photo_path not in published_paths:
                            self.s3_client.delete_object(
                                Bucket=self.bucket_name,
                                Key=key
                            )
                            print(f"Deleted thumbnail: {key}")
        except Exception as e:
            print(f"Error syncing thumbnails: {e}")

    def _export_and_upload_published_db(self) -> bool:
        """
        Export published photos to a separate SQLite database and upload to R2.
        This allows the deployed version to download a lightweight database
        instead of listing all R2 objects on startup.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create temporary database file
            temp_db = tempfile.NamedTemporaryFile(mode='w+b', suffix='.db', delete=False)
            temp_db_path = temp_db.name
            temp_db.close()

            # Connect to both databases
            source_db = get_db()
            export_db = sqlite3.connect(temp_db_path)
            export_cursor = export_db.cursor()

            # Create photos table in export database (matching source schema)
            export_cursor.execute('''
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

            # Copy only published photos
            source_cursor = source_db.execute(
                'SELECT * FROM photos WHERE published = 1'
            )

            # Get column names
            columns = [description[0] for description in source_cursor.description]

            # Insert published photos into export database
            for row in source_cursor:
                placeholders = ','.join(['?' for _ in columns])
                export_cursor.execute(
                    f'INSERT INTO photos ({",".join(columns)}) VALUES ({placeholders})',
                    row
                )

            export_db.commit()
            export_db.close()

            # Upload to R2
            print(f"Uploading published database to R2...")
            self.s3_client.upload_file(
                temp_db_path,
                self.bucket_name,
                'metadata/published.db',
                ExtraArgs={
                    'ContentType': 'application/x-sqlite3',
                    'CacheControl': 'no-cache'  # Always fetch latest
                }
            )

            # Clean up temp file
            Path(temp_db_path).unlink()

            return True

        except Exception as e:
            print(f"Error exporting published database: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _get_content_type(self, path: str) -> str:
        """
        Get content type based on file extension.
        """
        ext = Path(path).suffix.lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return content_types.get(ext, 'application/octet-stream')
