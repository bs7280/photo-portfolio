import { useState } from 'react';
import { updatePhotoMetadata, movePhoto, deletePhoto } from '../api/client';
import './BulkActionsBar.css';

export default function BulkActionsBar({
  selectedPhotos,
  totalPhotos,
  albums,
  onSelectAll,
  onClearSelection,
  onActionComplete
}) {
  const [targetAlbum, setTargetAlbum] = useState('');
  const [processing, setProcessing] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  const selectedCount = selectedPhotos.length;

  const handlePublish = async () => {
    setProcessing(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await Promise.all(
        selectedPhotos.map(photoId =>
          updatePhotoMetadata(photoId, { published: true })
        )
      );
      setSuccessMessage(`Published ${selectedCount} photos`);
      setTimeout(() => setSuccessMessage(null), 3000);
      if (onActionComplete) onActionComplete();
    } catch (err) {
      console.error('Error publishing photos:', err);
      setError('Failed to publish some photos');
    } finally {
      setProcessing(false);
    }
  };

  const handleUnpublish = async () => {
    setProcessing(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await Promise.all(
        selectedPhotos.map(photoId =>
          updatePhotoMetadata(photoId, { published: false })
        )
      );
      setSuccessMessage(`Unpublished ${selectedCount} photos`);
      setTimeout(() => setSuccessMessage(null), 3000);
      if (onActionComplete) onActionComplete();
    } catch (err) {
      console.error('Error unpublishing photos:', err);
      setError('Failed to unpublish some photos');
    } finally {
      setProcessing(false);
    }
  };

  const handleMove = async () => {
    if (!targetAlbum) return;

    setProcessing(true);
    setError(null);
    setSuccessMessage(null);

    try {
      // Convert "__root__" to null for API
      const albumValue = targetAlbum === '__root__' ? null : targetAlbum;

      await Promise.all(
        selectedPhotos.map(photoId =>
          movePhoto(photoId, albumValue)
        )
      );
      const albumName = targetAlbum === '__root__' ? 'Root' : targetAlbum;
      setSuccessMessage(`Moved ${selectedCount} photos to ${albumName}`);
      setTimeout(() => setSuccessMessage(null), 3000);
      setTargetAlbum('');
      if (onActionComplete) onActionComplete();
      if (onClearSelection) onClearSelection();
    } catch (err) {
      console.error('Error moving photos:', err);
      setError('Failed to move some photos');
    } finally {
      setProcessing(false);
    }
  };

  const handleDelete = async () => {
    setProcessing(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await Promise.all(
        selectedPhotos.map(photoId => deletePhoto(photoId))
      );
      setSuccessMessage(`Deleted ${selectedCount} photos`);
      setTimeout(() => setSuccessMessage(null), 3000);
      setShowDeleteConfirm(false);
      if (onActionComplete) onActionComplete();
      if (onClearSelection) onClearSelection();
    } catch (err) {
      console.error('Error deleting photos:', err);
      setError('Failed to delete some photos');
    } finally {
      setProcessing(false);
    }
  };

  if (selectedCount === 0) {
    return null;
  }

  return (
    <div className="bulk-actions-bar">
      <div className="bulk-actions-container">
        <div className="selection-info">
          <span className="selected-count">
            {selectedCount} of {totalPhotos} selected
          </span>
          <div className="selection-controls">
            {selectedCount < totalPhotos && (
              <button onClick={onSelectAll} className="btn-link">
                Select All
              </button>
            )}
            <button onClick={onClearSelection} className="btn-link">
              Clear Selection
            </button>
          </div>
        </div>

        <div className="bulk-actions">
          <button
            onClick={handlePublish}
            disabled={processing}
            className="btn btn-success"
          >
            {processing ? 'Publishing...' : 'Publish'}
          </button>

          <button
            onClick={handleUnpublish}
            disabled={processing}
            className="btn btn-warning"
          >
            {processing ? 'Unpublishing...' : 'Unpublish'}
          </button>

          <div className="move-control">
            <select
              value={targetAlbum}
              onChange={(e) => setTargetAlbum(e.target.value)}
              disabled={processing}
              className="album-select"
            >
              <option value="">Move to...</option>
              <option value="__root__">Root (No Album)</option>
              {albums.map(album => (
                <option key={album.id} value={album.id}>
                  {album.name}
                </option>
              ))}
            </select>
            {targetAlbum && (
              <button
                onClick={handleMove}
                disabled={processing}
                className="btn btn-primary"
              >
                {processing ? 'Moving...' : 'Move'}
              </button>
            )}
          </div>

          {!showDeleteConfirm ? (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              disabled={processing}
              className="btn btn-danger"
            >
              Delete
            </button>
          ) : (
            <div className="delete-confirm">
              <span>Delete {selectedCount} photos?</span>
              <button
                onClick={handleDelete}
                disabled={processing}
                className="btn btn-danger-confirm"
              >
                {processing ? 'Deleting...' : 'Confirm Delete'}
              </button>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                disabled={processing}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}
      {successMessage && <div className="success-message">{successMessage}</div>}
    </div>
  );
}
