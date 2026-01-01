import { useState } from 'react';
import { createAlbum, deleteAlbum } from '../api/client';
import './AlbumEditControls.css';

export function CreateAlbumButton({ onAlbumCreated }) {
  const [showForm, setShowForm] = useState(false);
  const [albumName, setAlbumName] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!albumName.trim()) {
      return;
    }

    setCreating(true);
    setError(null);

    try {
      await createAlbum(albumName.trim());
      setAlbumName('');
      setShowForm(false);
      if (onAlbumCreated) {
        onAlbumCreated();
      }
    } catch (err) {
      console.error('Error creating album:', err);
      setError(err.response?.data?.error || 'Failed to create album');
    } finally {
      setCreating(false);
    }
  };

  if (!showForm) {
    return (
      <button className="btn btn-primary" onClick={() => setShowForm(true)}>
        + Create Album
      </button>
    );
  }

  return (
    <div className="create-album-form">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={albumName}
          onChange={(e) => setAlbumName(e.target.value)}
          placeholder="Album name..."
          autoFocus
          disabled={creating}
        />
        <div className="form-actions">
          <button type="submit" disabled={creating || !albumName.trim()} className="btn btn-primary">
            {creating ? 'Creating...' : 'Create'}
          </button>
          <button
            type="button"
            onClick={() => {
              setShowForm(false);
              setAlbumName('');
              setError(null);
            }}
            disabled={creating}
            className="btn btn-secondary"
          >
            Cancel
          </button>
        </div>
      </form>
      {error && <div className="error-message">{error}</div>}
    </div>
  );
}

export function DeleteAlbumButton({ albumId, albumName, onAlbumDeleted }) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [deletePhotos, setDeletePhotos] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState(null);

  const handleDelete = async () => {
    setDeleting(true);
    setError(null);

    try {
      await deleteAlbum(albumId, deletePhotos);
      if (onAlbumDeleted) {
        onAlbumDeleted();
      }
    } catch (err) {
      console.error('Error deleting album:', err);
      setError(err.response?.data?.error || 'Failed to delete album');
    } finally {
      setDeleting(false);
    }
  };

  if (!showConfirm) {
    return (
      <button className="btn btn-danger btn-sm" onClick={() => setShowConfirm(true)}>
        Delete Album
      </button>
    );
  }

  return (
    <div className="delete-album-confirm">
      <div className="confirm-message">
        Delete album "{albumName}"?
      </div>

      <label className="checkbox-label">
        <input
          type="checkbox"
          checked={deletePhotos}
          onChange={(e) => setDeletePhotos(e.target.checked)}
          disabled={deleting}
        />
        <span>Also delete all photos in this album</span>
      </label>

      <div className="confirm-actions">
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="btn btn-danger-confirm"
        >
          {deleting ? 'Deleting...' : 'Yes, Delete'}
        </button>
        <button
          onClick={() => {
            setShowConfirm(false);
            setDeletePhotos(false);
            setError(null);
          }}
          disabled={deleting}
          className="btn btn-secondary"
        >
          Cancel
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}
