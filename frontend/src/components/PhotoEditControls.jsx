import { useState, useEffect } from 'react';
import { updatePhotoMetadata, movePhoto, deletePhoto } from '../api/client';
import './PhotoEditControls.css';

export default function PhotoEditControls({ photo, albums, onUpdate, onDelete, onClose }) {
  const [formData, setFormData] = useState({
    published: photo.published || false,
    custom_title: photo.custom_title || '',
    description: photo.description || '',
    tags: photo.tags || [],
    notes: photo.notes || ''
  });
  const [tagInput, setTagInput] = useState('');
  const [selectedAlbum, setSelectedAlbum] = useState(photo.album || '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleAddTag = (e) => {
    e.preventDefault();
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, tagInput.trim()]
      }));
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleSaveMetadata = async () => {
    setSaving(true);
    setError(null);

    try {
      await updatePhotoMetadata(photo.id, formData);
      if (onUpdate) {
        onUpdate();
      }
    } catch (err) {
      console.error('Error saving metadata:', err);
      setError('Failed to save metadata');
    } finally {
      setSaving(false);
    }
  };

  const handleMovePhoto = async () => {
    if (selectedAlbum === photo.album) {
      return; // No change
    }

    setSaving(true);
    setError(null);

    try {
      await movePhoto(photo.id, selectedAlbum || null);
      if (onUpdate) {
        onUpdate();
      }
      if (onClose) {
        onClose();
      }
    } catch (err) {
      console.error('Error moving photo:', err);
      setError('Failed to move photo');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    setSaving(true);
    setError(null);

    try {
      await deletePhoto(photo.id);
      if (onDelete) {
        onDelete();
      }
      if (onClose) {
        onClose();
      }
    } catch (err) {
      console.error('Error deleting photo:', err);
      setError('Failed to delete photo');
      setSaving(false);
    }
  };

  return (
    <div className="photo-edit-controls">
      <h3>Edit Photo</h3>

      {error && <div className="error-message">{error}</div>}

      <div className="edit-section">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={formData.published}
            onChange={(e) => handleChange('published', e.target.checked)}
          />
          <span className="checkbox-text">
            {formData.published ? '✓ Published (whitelisted)' : '✗ Unpublished'}
          </span>
        </label>
      </div>

      <div className="edit-section">
        <label>
          Custom Title
          <input
            type="text"
            value={formData.custom_title}
            onChange={(e) => handleChange('custom_title', e.target.value)}
            placeholder="Optional custom title"
          />
        </label>
      </div>

      <div className="edit-section">
        <label>
          Description
          <textarea
            value={formData.description}
            onChange={(e) => handleChange('description', e.target.value)}
            placeholder="Photo description"
            rows="3"
          />
        </label>
      </div>

      <div className="edit-section">
        <label>Tags</label>
        <div className="tags-container">
          {formData.tags.map(tag => (
            <span key={tag} className="tag">
              {tag}
              <button
                type="button"
                className="tag-remove"
                onClick={() => handleRemoveTag(tag)}
              >
                ×
              </button>
            </span>
          ))}
        </div>
        <form onSubmit={handleAddTag} className="tag-input-form">
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            placeholder="Add tag..."
          />
          <button type="submit" disabled={!tagInput.trim()}>
            Add
          </button>
        </form>
      </div>

      <div className="edit-section">
        <label>
          Notes
          <textarea
            value={formData.notes}
            onChange={(e) => handleChange('notes', e.target.value)}
            placeholder="Private notes"
            rows="2"
          />
        </label>
      </div>

      <div className="edit-section">
        <label>
          Move to Album
          <select
            value={selectedAlbum}
            onChange={(e) => setSelectedAlbum(e.target.value)}
          >
            <option value="">Root (No Album)</option>
            {albums.map(album => (
              <option key={album.id} value={album.id}>
                {album.name}
              </option>
            ))}
          </select>
        </label>
        {selectedAlbum !== photo.album && (
          <button
            onClick={handleMovePhoto}
            disabled={saving}
            className="btn btn-secondary"
          >
            {saving ? 'Moving...' : 'Move Photo'}
          </button>
        )}
      </div>

      <div className="edit-actions">
        <button
          onClick={handleSaveMetadata}
          disabled={saving}
          className="btn btn-primary"
        >
          {saving ? 'Saving...' : 'Save Metadata'}
        </button>

        {!showDeleteConfirm ? (
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="btn btn-danger"
          >
            Delete Photo
          </button>
        ) : (
          <div className="delete-confirm">
            <span>Are you sure?</span>
            <button
              onClick={handleDelete}
              disabled={saving}
              className="btn btn-danger-confirm"
            >
              {saving ? 'Deleting...' : 'Yes, Delete'}
            </button>
            <button
              onClick={() => setShowDeleteConfirm(false)}
              className="btn btn-secondary"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
