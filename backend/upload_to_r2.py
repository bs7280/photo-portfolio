#!/usr/bin/env python3
"""
Upload photos to Cloudflare R2 bucket with thumbnail generation
Usage: python upload_to_r2.py
"""
import os
import sys
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from PIL import Image
import io

# Load environment variables
load_dotenv()

# R2 Configuration
R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID')
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME', 'photography-portfolio')
R2_ENDPOINT_URL = os.getenv('R2_ENDPOINT_URL')

# Validate configuration
if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT_URL]):
    print("❌ Error: Missing R2 configuration in .env file")
    print("Required variables: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT_URL")
    sys.exit(1)

# Supported image extensions
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

# Thumbnail size (max width/height)
THUMBNAIL_SIZE = (800, 800)

def get_s3_client():
    """Create and return S3 client for R2"""
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name='auto'
    )

def get_content_type(file_path):
    """Get content type based on file extension"""
    ext = file_path.suffix.lower()
    content_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    return content_types.get(ext, 'application/octet-stream')

def generate_thumbnail(image_path):
    """Generate a thumbnail for an image"""
    try:
        img = Image.open(image_path)

        # Convert RGBA to RGB if needed (for PNG with transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background

        # Create thumbnail maintaining aspect ratio
        img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

        # Save to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85, optimize=True)
        buffer.seek(0)

        return buffer
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return None

def upload_file(s3_client, file_path, key):
    """Upload a single file to R2"""
    try:
        content_type = get_content_type(file_path)
        s3_client.upload_file(
            str(file_path),
            R2_BUCKET_NAME,
            key,
            ExtraArgs={
                'ContentType': content_type,
                'CacheControl': 'public, max-age=31536000'  # Cache for 1 year
            }
        )
        return True
    except ClientError as e:
        print(f"❌ Error uploading {file_path}: {e}")
        return False

def upload_thumbnail(s3_client, file_path, key):
    """Generate and upload a thumbnail to R2"""
    try:
        thumbnail_buffer = generate_thumbnail(file_path)
        if not thumbnail_buffer:
            return False

        s3_client.upload_fileobj(
            thumbnail_buffer,
            R2_BUCKET_NAME,
            f"thumbnails/{key}",
            ExtraArgs={
                'ContentType': 'image/jpeg',
                'CacheControl': 'public, max-age=31536000'
            }
        )
        return True
    except ClientError as e:
        print(f"❌ Error uploading thumbnail: {e}")
        return False

def upload_photos(photos_dir='./photos'):
    """Upload all photos from photos directory to R2"""
    photos_path = Path(photos_dir)

    if not photos_path.exists():
        print(f"❌ Photos directory not found: {photos_dir}")
        sys.exit(1)

    print(f"📁 Scanning photos directory: {photos_path}")

    # Get S3 client
    s3_client = get_s3_client()

    # Find all image files
    image_files = []
    for file_path in photos_path.rglob('*'):
        if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            image_files.append(file_path)

    if not image_files:
        print(f"❌ No images found in {photos_dir}")
        sys.exit(1)

    print(f"📸 Found {len(image_files)} images to upload")
    print()

    # Upload files
    uploaded = 0
    failed = 0

    for i, file_path in enumerate(image_files, 1):
        # Create R2 key (preserve folder structure)
        relative_path = file_path.relative_to(photos_path)
        key = str(relative_path).replace('\\', '/')

        print(f"[{i}/{len(image_files)}] {key}")

        # Upload full-size image
        print(f"  → Full size...", end=' ')
        if upload_file(s3_client, file_path, key):
            print("✅")

            # Upload thumbnail
            print(f"  → Thumbnail...", end=' ')
            if upload_thumbnail(s3_client, file_path, key):
                print("✅")
                uploaded += 1
            else:
                print("❌ (thumbnail failed)")
                failed += 1
        else:
            print("❌")
            failed += 1

    print()
    print("=" * 50)
    print(f"✅ Upload complete!")
    print(f"   Uploaded: {uploaded}")
    if failed > 0:
        print(f"   Failed: {failed}")
    print("=" * 50)
    print()
    print(f"🌐 Your photos are now available at:")
    print(f"   {os.getenv('R2_PUBLIC_URL')}")
    print()
    print("📝 Next steps:")
    print("   1. Update your .env file:")
    print("      USE_CDN=true")
    print(f"      CDN_BASE_URL={os.getenv('R2_PUBLIC_URL')}")
    print("   2. Restart your backend server")

if __name__ == '__main__':
    upload_photos()
