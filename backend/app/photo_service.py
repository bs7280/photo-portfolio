import os
import shutil
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
from typing import List, Dict, Optional
from app.config import Config
from app.database import (
    get_photo_metadata, get_all_photo_metadata, create_photo_metadata,
    update_photo_metadata, delete_photo_metadata, sync_photos_to_db,
    get_album_metadata, get_all_album_metadata, create_album_metadata,
    update_album_metadata, delete_album_metadata
)
from app.thumbnail_service import ThumbnailService
import boto3

class PhotoService:
    def __init__(self):
        self.photos_dir = Path(Config.PHOTOS_DIR)
        self.use_cdn = Config.USE_CDN
        self.cdn_base_url = Config.CDN_BASE_URL
        self.thumbnail_service = ThumbnailService()

        # Initialize R2 client if using CDN
        if self.use_cdn and Config.R2_ACCESS_KEY_ID:
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

    def get_photo_url(self, relative_path: str, is_thumbnail: bool = False) -> str:
        """Generate URL for a photo (local or CDN)"""
        if self.use_cdn:
            # For CDN, thumbnails are in thumbnails/ folder, full images at root
            if is_thumbnail:
                return f"{self.cdn_base_url}/thumbnails/{relative_path}"
            else:
                return f"{self.cdn_base_url}/{relative_path}"
        else:
            prefix = 'thumbnails' if is_thumbnail else 'photos'
            return f"{Config.BACKEND_URL}/api/{prefix}/{relative_path}"

    def extract_metadata(self, image_path: Path) -> Dict:
        """Extract EXIF metadata from image"""
        try:
            image = Image.open(image_path)
            exif_data = {}

            if hasattr(image, '_getexif') and image._getexif():
                exif = image._getexif()
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = str(value)

            width, height = image.size

            return {
                'width': width,
                'height': height,
                'aspect_ratio': width / height if height > 0 else 1,
                'camera': exif_data.get('Model', 'Unknown'),
                'lens': exif_data.get('LensModel', 'Unknown'),
                'iso': exif_data.get('ISOSpeedRatings', 'Unknown'),
                'aperture': exif_data.get('FNumber', 'Unknown'),
                'shutter_speed': exif_data.get('ExposureTime', 'Unknown'),
                'date_taken': exif_data.get('DateTimeOriginal', exif_data.get('DateTime', 'Unknown')),
                'orientation': exif_data.get('Orientation', '1')
            }
        except Exception as e:
            print(f"Error extracting metadata from {image_path}: {e}")
            return {}

    def _list_r2_objects(self) -> List[str]:
        """List all photo objects in R2 bucket"""
        if not self.s3_client:
            return []

        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            objects = []

            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    # Skip thumbnails folder and only include supported extensions
                    if not key.startswith('thumbnails/'):
                        ext = os.path.splitext(key)[1].lower()
                        if ext in Config.SUPPORTED_EXTENSIONS:
                            objects.append(key)

            return objects
        except Exception as e:
            print(f"Error listing R2 objects: {e}")
            return []

    def _get_album_name_from_path(self, path: str) -> Optional[str]:
        """Extract album name from path string (works for both R2 keys and local paths)"""
        parts = path.split('/')
        if len(parts) > 1:
            return parts[0]
        return None

    def get_all_photos(self) -> List[Dict]:
        """Get all photos with their metadata (EXIF + database)"""
        photos = []

        # Use R2 when CDN is enabled - read from downloaded published database
        if self.use_cdn and self.s3_client:
            # Get all photos from database (which was downloaded from R2 on startup)
            # This is much faster than listing R2 objects
            all_db_photos = get_all_photo_metadata()

            for db_meta in all_db_photos:
                path = db_meta['path']
                filename = os.path.basename(path)

                photos.append({
                    'id': path.replace('/', '_').replace('\\', '_'),
                    'filename': filename,
                    'path': path,
                    'url': self.get_photo_url(path),
                    'thumbnail_url': self.get_photo_url(path, is_thumbnail=True),
                    'metadata': db_meta.get('exif_data', {}),  # EXIF stored in database
                    'album': self._get_album_name_from_path(path),
                    # All photos in published database are published
                    'published': True,
                    'custom_title': db_meta.get('custom_title'),
                    'description': db_meta.get('description'),
                    'tags': db_meta.get('tags', []),
                    'notes': db_meta.get('notes')
                })

            return sorted(photos, key=lambda x: x.get('filename', ''))

        # Use local filesystem when CDN is disabled
        if not self.photos_dir.exists():
            return photos

        for image_path in self.photos_dir.rglob('*'):
            if image_path.suffix.lower() in Config.SUPPORTED_EXTENSIONS:
                relative_path = str(image_path.relative_to(self.photos_dir))

                # Extract EXIF metadata
                exif_metadata = self.extract_metadata(image_path)

                # Get custom metadata from database
                db_meta = get_photo_metadata(relative_path) or {}

                # Filter by published flag if not in edit mode
                if not Config.EDIT_MODE and not db_meta.get('published', False):
                    continue

                photos.append({
                    'id': relative_path.replace('/', '_').replace('\\', '_'),
                    'filename': image_path.name,
                    'path': relative_path,
                    'url': self.get_photo_url(relative_path),
                    'thumbnail_url': self.get_photo_url(relative_path, is_thumbnail=True),
                    'metadata': exif_metadata,
                    'album': self._get_album_name_from_path(relative_path),
                    # Add custom metadata from database
                    'published': db_meta.get('published', False),
                    'custom_title': db_meta.get('custom_title'),
                    'description': db_meta.get('description'),
                    'tags': db_meta.get('tags', []),
                    'notes': db_meta.get('notes')
                })

        return sorted(photos, key=lambda x: x['metadata'].get('date_taken', ''), reverse=True)

    def _get_album_name(self, image_path: Path) -> Optional[str]:
        """Extract album name from folder structure"""
        relative_path = image_path.relative_to(self.photos_dir)
        if len(relative_path.parts) > 1:
            return relative_path.parts[0]
        return None

    def get_albums(self) -> List[Dict]:
        """Get all albums based on folder structure and database"""
        albums = {}

        # Use R2 when CDN is enabled
        if self.use_cdn and self.s3_client:
            for key in self._list_r2_objects():
                album_name = self._get_album_name_from_path(key)

                if album_name:
                    if album_name not in albums:
                        albums[album_name] = {
                            'id': album_name,
                            'name': album_name,
                            'photo_count': 0,
                            'cover_photo': None
                        }

                    albums[album_name]['photo_count'] += 1

                    if albums[album_name]['cover_photo'] is None:
                        albums[album_name]['cover_photo'] = self.get_photo_url(key, is_thumbnail=True)

            return sorted(albums.values(), key=lambda x: x['name'])

        # Use local filesystem when CDN is disabled
        if self.photos_dir.exists():
            for image_path in self.photos_dir.rglob('*'):
                if image_path.suffix.lower() in Config.SUPPORTED_EXTENSIONS:
                    album_name = self._get_album_name(image_path)

                    if album_name:
                        if album_name not in albums:
                            albums[album_name] = {
                                'id': album_name,
                                'name': album_name,
                                'photo_count': 0,
                                'cover_photo': None
                            }

                        albums[album_name]['photo_count'] += 1

                        if albums[album_name]['cover_photo'] is None:
                            relative_path = str(image_path.relative_to(self.photos_dir))
                            albums[album_name]['cover_photo'] = self.get_photo_url(relative_path, is_thumbnail=True)

        # Also include empty albums from database
        db_albums = get_all_album_metadata()
        for db_album in db_albums:
            album_name = db_album['name']
            if album_name not in albums:
                # Empty album - add it with 0 photos
                albums[album_name] = {
                    'id': album_name,
                    'name': db_album.get('display_name') or album_name,
                    'photo_count': 0,
                    'cover_photo': None
                }

        return sorted(albums.values(), key=lambda x: x['name'])

    def get_album_photos(self, album_id: str) -> List[Dict]:
        """Get all photos in a specific album"""
        all_photos = self.get_all_photos()
        return [photo for photo in all_photos if photo['album'] == album_id]

    # Edit operations (only available when EDIT_MODE=true)

    def move_photo(self, photo_path: str, target_album: Optional[str]) -> bool:
        """
        Move a photo to a different album (or root if target_album is None).

        Args:
            photo_path: Current path to photo (relative to PHOTOS_DIR)
            target_album: Target album name, or None for root directory

        Returns:
            True if successful, False otherwise
        """
        if not Config.EDIT_MODE:
            raise PermissionError("Edit mode is disabled")

        try:
            source_path = self.photos_dir / photo_path
            if not source_path.exists():
                print(f"Source file not found: {source_path}")
                return False

            # Build target path
            filename = source_path.name
            if target_album:
                target_dir = self.photos_dir / target_album
                target_dir.mkdir(exist_ok=True)
                target_path = target_dir / filename
            else:
                target_path = self.photos_dir / filename

            # Get existing metadata before moving
            old_metadata = get_photo_metadata(photo_path)

            # Move file on disk
            shutil.move(str(source_path), str(target_path))

            # Move thumbnail if it exists
            old_thumbnail_path = self.thumbnail_service.get_thumbnail_path(photo_path)
            if old_thumbnail_path.exists():
                new_relative_path = str(target_path.relative_to(self.photos_dir))
                new_thumbnail_path = self.thumbnail_service.get_thumbnail_path(new_relative_path)
                new_thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_thumbnail_path), str(new_thumbnail_path))

            # Update database - delete old record and create new one
            new_relative_path = str(target_path.relative_to(self.photos_dir))

            # Delete old record
            delete_photo_metadata(photo_path)

            # Create new record with updated path and album
            create_photo_metadata(
                path=new_relative_path,
                filename=filename,
                album=target_album,
                published=old_metadata.get('published', False) if old_metadata else False,
                exif_data=old_metadata.get('exif_data') if old_metadata else None
            )

            # If there was custom metadata, restore it
            if old_metadata:
                custom_fields = {
                    'custom_title': old_metadata.get('custom_title'),
                    'description': old_metadata.get('description'),
                    'tags': old_metadata.get('tags', []),
                    'notes': old_metadata.get('notes')
                }
                # Filter out None values
                custom_fields = {k: v for k, v in custom_fields.items() if v}
                if custom_fields:
                    update_photo_metadata(new_relative_path, custom_fields)

            return True

        except Exception as e:
            print(f"Error moving photo {photo_path} to {target_album}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def delete_photo(self, photo_path: str) -> bool:
        """
        Delete a photo from disk and database.

        Args:
            photo_path: Path to photo (relative to PHOTOS_DIR)

        Returns:
            True if successful, False otherwise
        """
        if not Config.EDIT_MODE:
            raise PermissionError("Edit mode is disabled")

        try:
            file_path = self.photos_dir / photo_path
            if not file_path.exists():
                return False

            # Delete file from disk
            file_path.unlink()

            # Delete thumbnail if it exists
            self.thumbnail_service.delete_thumbnail(photo_path)

            # Delete from database
            delete_photo_metadata(photo_path)

            return True

        except Exception as e:
            print(f"Error deleting photo {photo_path}: {e}")
            return False

    def create_album(self, album_name: str) -> bool:
        """
        Create a new album (directory).

        Args:
            album_name: Name of album to create

        Returns:
            True if successful, False otherwise
        """
        if not Config.EDIT_MODE:
            raise PermissionError("Edit mode is disabled")

        try:
            album_dir = self.photos_dir / album_name
            if album_dir.exists():
                return False  # Album already exists

            album_dir.mkdir(parents=True)

            # Create metadata record
            create_album_metadata(name=album_name, published=True)

            return True

        except Exception as e:
            print(f"Error creating album {album_name}: {e}")
            return False

    def update_photo_custom_metadata(self, photo_path: str, metadata: Dict) -> bool:
        """
        Update custom metadata for a photo in database.

        Args:
            photo_path: Path to photo (relative to PHOTOS_DIR)
            metadata: Dict with custom fields (published, custom_title, description, tags, notes)

        Returns:
            True if successful, False otherwise
        """
        if not Config.EDIT_MODE:
            raise PermissionError("Edit mode is disabled")

        try:
            return update_photo_metadata(photo_path, metadata)
        except Exception as e:
            print(f"Error updating photo metadata for {photo_path}: {e}")
            return False

    def sync_database(self) -> Dict[str, int]:
        """
        Sync database with filesystem. Adds missing photos, removes orphaned records.

        Returns:
            Dict with 'added' and 'removed' counts
        """
        try:
            # Build list of photos from filesystem with EXIF data
            photos_list = []

            for image_path in self.photos_dir.rglob('*'):
                if image_path.suffix.lower() in Config.SUPPORTED_EXTENSIONS:
                    relative_path = str(image_path.relative_to(self.photos_dir))
                    album_name = self._get_album_name(image_path)

                    # Extract EXIF data for storage
                    exif_data = self.extract_metadata(image_path)

                    photos_list.append({
                        'path': relative_path,
                        'filename': image_path.name,
                        'album': album_name,
                        'exif_data': exif_data
                    })

            # Sync with database
            return sync_photos_to_db(photos_list)

        except Exception as e:
            print(f"Error syncing database: {e}")
            return {'added': 0, 'removed': 0}

    def delete_album(self, album_name: str, delete_photos: bool = False) -> bool:
        """
        Delete an album. Optionally delete all photos in the album.

        Args:
            album_name: Name of album to delete
            delete_photos: If True, delete all photos in album. If False, move photos to root.

        Returns:
            True if successful, False otherwise
        """
        if not Config.EDIT_MODE:
            raise PermissionError("Edit mode is disabled")

        try:
            album_dir = self.photos_dir / album_name
            if not album_dir.exists() or not album_dir.is_dir():
                return False

            if delete_photos:
                # Delete entire directory and all photos
                shutil.rmtree(album_dir)

                # Delete all photo metadata from database
                album_photos = self.get_album_photos(album_name)
                for photo in album_photos:
                    delete_photo_metadata(photo['path'])
            else:
                # Move photos to root directory
                for file_path in album_dir.iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in Config.SUPPORTED_EXTENSIONS:
                        target_path = self.photos_dir / file_path.name
                        shutil.move(str(file_path), str(target_path))

                        # Update database
                        old_path = str(file_path.relative_to(self.photos_dir))
                        update_photo_metadata(old_path, {
                            'path': file_path.name,
                            'album': None
                        })

                # Remove empty directory
                album_dir.rmdir()

            # Delete album metadata
            delete_album_metadata(album_name)

            return True

        except Exception as e:
            print(f"Error deleting album {album_name}: {e}")
            return False
