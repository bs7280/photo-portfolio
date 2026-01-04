"""
Service for generating and managing photo thumbnails.
"""
from pathlib import Path
from PIL import Image, ImageOps
from typing import Optional
from app.config import Config


class ThumbnailService:
    def __init__(self):
        self.photos_dir = Path(Config.PHOTOS_DIR).resolve()
        self.thumbnails_dir = self.photos_dir.parent / 'thumbnails'
        self.thumbnail_size = Config.THUMBNAIL_SIZE  # (400, 400)

    def ensure_thumbnails_dir(self):
        """Ensure thumbnails directory exists."""
        self.thumbnails_dir.mkdir(exist_ok=True)

    def get_thumbnail_path(self, photo_path: str) -> Path:
        """
        Get the filesystem path for a thumbnail.

        Args:
            photo_path: Relative path to photo (e.g., "Chicago/IMG_123.jpg")

        Returns:
            Absolute path to thumbnail file
        """
        return self.thumbnails_dir / photo_path

    def generate_thumbnail(self, photo_path: str, force: bool = False) -> Optional[Path]:
        """
        Generate a thumbnail for a photo.

        Args:
            photo_path: Relative path to photo from PHOTOS_DIR
            force: If True, regenerate even if thumbnail exists

        Returns:
            Path to generated thumbnail, or None if failed
        """
        try:
            # Source photo
            source_path = self.photos_dir / photo_path
            if not source_path.exists():
                print(f"Source photo not found: {source_path}")
                return None

            # Thumbnail destination
            thumbnail_path = self.get_thumbnail_path(photo_path)

            # Skip if thumbnail already exists (unless force)
            if thumbnail_path.exists() and not force:
                return thumbnail_path

            # Ensure parent directory exists
            thumbnail_path.parent.mkdir(parents=True, exist_ok=True)

            # Open and resize image
            with Image.open(source_path) as img:
                # Apply EXIF orientation (fixes iPhone photo rotation)
                img = ImageOps.exif_transpose(img)

                # Convert RGBA to RGB if necessary (for JPEG)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Resize maintaining aspect ratio
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)

                # Save as JPEG with good quality
                img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)

            print(f"Generated thumbnail: {photo_path}")
            return thumbnail_path

        except Exception as e:
            print(f"Error generating thumbnail for {photo_path}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def generate_all_thumbnails(self, photo_paths: list[str], force: bool = False) -> dict:
        """
        Generate thumbnails for a list of photos.

        Args:
            photo_paths: List of relative photo paths
            force: If True, regenerate existing thumbnails

        Returns:
            Dict with 'generated', 'skipped', 'failed' counts
        """
        result = {
            'generated': 0,
            'skipped': 0,
            'failed': 0,
            'total': len(photo_paths)
        }

        for photo_path in photo_paths:
            thumbnail_path = self.get_thumbnail_path(photo_path)

            # Skip if exists and not forcing
            if thumbnail_path.exists() and not force:
                result['skipped'] += 1
                continue

            # Generate thumbnail
            if self.generate_thumbnail(photo_path, force=force):
                result['generated'] += 1
            else:
                result['failed'] += 1

        return result

    def delete_thumbnail(self, photo_path: str) -> bool:
        """
        Delete a thumbnail.

        Args:
            photo_path: Relative path to photo

        Returns:
            True if deleted, False if not found
        """
        try:
            thumbnail_path = self.get_thumbnail_path(photo_path)
            if thumbnail_path.exists():
                thumbnail_path.unlink()
                print(f"Deleted thumbnail: {photo_path}")
                return True
            return False
        except Exception as e:
            print(f"Error deleting thumbnail for {photo_path}: {e}")
            return False

    def cleanup_orphaned_thumbnails(self, valid_photo_paths: set[str]) -> int:
        """
        Delete thumbnails that don't have corresponding photos.

        Args:
            valid_photo_paths: Set of valid photo paths that should have thumbnails

        Returns:
            Number of orphaned thumbnails deleted
        """
        deleted = 0

        if not self.thumbnails_dir.exists():
            return 0

        # Walk through thumbnails directory
        for thumbnail_file in self.thumbnails_dir.rglob('*'):
            if thumbnail_file.is_file():
                # Get relative path
                rel_path = str(thumbnail_file.relative_to(self.thumbnails_dir))

                # Delete if photo doesn't exist
                if rel_path not in valid_photo_paths:
                    thumbnail_file.unlink()
                    deleted += 1
                    print(f"Cleaned up orphaned thumbnail: {rel_path}")

        return deleted
