from flask import Blueprint, jsonify, send_from_directory, current_app, request
from pathlib import Path
from app.photo_service import PhotoService
from app.sync_service import SyncService
from app.thumbnail_service import ThumbnailService
from app.config import Config

bp = Blueprint('api', __name__, url_prefix='/api')
photo_service = PhotoService()
thumbnail_service = ThumbnailService()

@bp.route('/photos', methods=['GET'])
def get_photos():
    """Get all photos"""
    photos = photo_service.get_all_photos()
    return jsonify(photos)

@bp.route('/albums', methods=['GET'])
def get_albums():
    """Get all albums"""
    albums = photo_service.get_albums()
    return jsonify(albums)

@bp.route('/albums/<album_id>/photos', methods=['GET'])
def get_album_photos(album_id):
    """Get photos for a specific album"""
    photos = photo_service.get_album_photos(album_id)
    return jsonify(photos)

@bp.route('/photos/<path:filename>', methods=['GET'])
def serve_photo(filename):
    """Serve a photo file (only for local development)"""
    if Config.USE_CDN:
        return jsonify({'error': 'Photos are served from CDN'}), 404

    photos_dir = Path(Config.PHOTOS_DIR).resolve()
    return send_from_directory(photos_dir, filename)

@bp.route('/thumbnails/<path:filename>', methods=['GET'])
def serve_thumbnail(filename):
    """Serve a thumbnail (only for local development)"""
    if Config.USE_CDN:
        return jsonify({'error': 'Thumbnails are served from CDN'}), 404

    # Generate thumbnail if it doesn't exist
    thumbnail_path = thumbnail_service.get_thumbnail_path(filename)

    if not thumbnail_path.exists():
        # Generate thumbnail on-demand
        generated_path = thumbnail_service.generate_thumbnail(filename)
        if not generated_path:
            # Fallback to serving original photo if thumbnail generation fails
            photos_dir = Path(Config.PHOTOS_DIR).resolve()
            return send_from_directory(photos_dir, filename)

    # Serve the thumbnail
    thumbnails_dir = thumbnail_service.thumbnails_dir
    return send_from_directory(thumbnails_dir, filename)

@bp.route('/config', methods=['GET'])
def get_config():
    """Get runtime configuration"""
    return jsonify({
        'edit_mode': Config.EDIT_MODE,
        'use_cdn': Config.USE_CDN
    })

# Edit mode endpoints (only available when EDIT_MODE=true)

def _get_photo_path_from_id(photo_id: str) -> str:
    """
    Convert photo ID back to actual path by looking it up in photos list.
    This handles filenames with underscores correctly.
    """
    photos = photo_service.get_all_photos()
    photo = next((p for p in photos if p['id'] == photo_id), None)
    if photo:
        return photo['path']
    # Fallback: assume simple path if not found
    return photo_id.replace('_', '/')

@bp.route('/photos/<path:photo_id>/metadata', methods=['POST'])
def update_photo_metadata(photo_id):
    """Update custom metadata for a photo"""
    if not Config.EDIT_MODE:
        return jsonify({'error': 'Edit mode is disabled'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Get actual path from photo ID
    photo_path = _get_photo_path_from_id(photo_id)

    # Update metadata
    success = photo_service.update_photo_custom_metadata(photo_path, data)

    if success:
        # Return updated photo data
        photos = photo_service.get_all_photos()
        updated_photo = next((p for p in photos if p['path'] == photo_path), None)
        return jsonify(updated_photo or {'success': True})
    else:
        return jsonify({'error': 'Failed to update metadata'}), 500

@bp.route('/photos/<path:photo_id>/move', methods=['POST'])
def move_photo(photo_id):
    """Move a photo to a different album"""
    if not Config.EDIT_MODE:
        return jsonify({'error': 'Edit mode is disabled'}), 403

    data = request.get_json()
    if not data or 'album' not in data:
        return jsonify({'error': 'Target album not specified'}), 400

    # Get actual path from photo ID
    photo_path = _get_photo_path_from_id(photo_id)
    target_album = data['album'] if data['album'] else None

    success = photo_service.move_photo(photo_path, target_album)

    if success:
        return jsonify({'success': True, 'message': 'Photo moved successfully'})
    else:
        return jsonify({'error': 'Failed to move photo'}), 500

@bp.route('/photos/<path:photo_id>', methods=['DELETE'])
def delete_photo(photo_id):
    """Delete a photo"""
    if not Config.EDIT_MODE:
        return jsonify({'error': 'Edit mode is disabled'}), 403

    # Get actual path from photo ID
    photo_path = _get_photo_path_from_id(photo_id)

    success = photo_service.delete_photo(photo_path)

    if success:
        return jsonify({'success': True, 'message': 'Photo deleted successfully'})
    else:
        return jsonify({'error': 'Failed to delete photo'}), 500

@bp.route('/albums', methods=['POST'])
def create_album():
    """Create a new album"""
    if not Config.EDIT_MODE:
        return jsonify({'error': 'Edit mode is disabled'}), 403

    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Album name not provided'}), 400

    album_name = data['name']

    success = photo_service.create_album(album_name)

    if success:
        return jsonify({'success': True, 'message': 'Album created successfully', 'album': album_name}), 201
    else:
        return jsonify({'error': 'Failed to create album (may already exist)'}), 400

@bp.route('/albums/<album_id>', methods=['PUT'])
def update_album(album_id):
    """Update album metadata"""
    if not Config.EDIT_MODE:
        return jsonify({'error': 'Edit mode is disabled'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    from app.database import update_album_metadata
    success = update_album_metadata(album_id, data)

    if success:
        return jsonify({'success': True, 'message': 'Album updated successfully'})
    else:
        return jsonify({'error': 'Failed to update album'}), 500

@bp.route('/albums/<album_id>', methods=['DELETE'])
def delete_album(album_id):
    """Delete an album"""
    if not Config.EDIT_MODE:
        return jsonify({'error': 'Edit mode is disabled'}), 403

    data = request.get_json() or {}
    delete_photos = data.get('delete_photos', False)

    success = photo_service.delete_album(album_id, delete_photos=delete_photos)

    if success:
        return jsonify({'success': True, 'message': 'Album deleted successfully'})
    else:
        return jsonify({'error': 'Failed to delete album'}), 500

@bp.route('/sync', methods=['POST'])
def sync_database():
    """Sync database with filesystem"""
    if not Config.EDIT_MODE:
        return jsonify({'error': 'Edit mode is disabled'}), 403

    result = photo_service.sync_database()

    return jsonify({
        'success': True,
        'message': f"Synced database: added {result['added']}, removed {result['removed']}",
        'added': result['added'],
        'removed': result['removed']
    })

@bp.route('/deploy', methods=['POST'])
def deploy_to_r2():
    """Deploy published photos to R2 bucket"""
    if not Config.EDIT_MODE:
        return jsonify({'error': 'Edit mode is disabled'}), 403

    if not Config.R2_ACCESS_KEY_ID:
        return jsonify({
            'success': False,
            'error': 'R2 credentials not configured'
        }), 400

    sync_service = SyncService()
    result = sync_service.sync_to_r2()

    status_code = 200 if result['success'] else 500
    return jsonify(result), status_code

@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})
