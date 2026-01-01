import { useState, useEffect } from 'react';
import { useEditMode } from '../context/EditModeContext';
import './PhotoGrid.css';

const PhotoGrid = ({ photos, onPhotoClick, selectedPhotos = [], onToggleSelect }) => {
  const { editMode } = useEditMode();

  const handlePhotoClick = (photo) => {
    // In edit mode, clicking the photo itself (not checkbox) still opens lightbox
    if (onPhotoClick) {
      onPhotoClick(photo);
    }
  };

  const handleCheckboxClick = (e, photoId) => {
    e.stopPropagation(); // Prevent opening lightbox
    if (onToggleSelect) {
      onToggleSelect(photoId);
    }
  };

  return (
    <div className="photo-grid">
      {photos.map((photo) => {
        const isSelected = selectedPhotos.includes(photo.id);

        return (
          <div
            key={photo.id}
            className={`photo-item ${isSelected ? 'selected' : ''}`}
            onClick={() => handlePhotoClick(photo)}
            style={{
              aspectRatio: photo.metadata.aspect_ratio || 1,
            }}
          >
            <img
              src={photo.thumbnail_url}
              alt={photo.filename}
              loading="lazy"
            />

            {/* Album badge - always visible */}
            {photo.album && (
              <div className="album-badge">
                {photo.album}
              </div>
            )}

            {/* Edit mode overlays */}
            {editMode && (
              <>
                <div className="photo-checkbox-overlay">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={(e) => handleCheckboxClick(e, photo.id)}
                    onClick={(e) => e.stopPropagation()}
                    className="photo-checkbox"
                  />
                </div>

                {!photo.published && (
                  <div className="unpublished-indicator">
                    Unpublished
                  </div>
                )}
              </>
            )}

            {/* Existing metadata overlay */}
            {photo.metadata.camera && photo.metadata.camera !== 'Unknown' && (
              <div className="photo-overlay">
                <div className="photo-info">
                  <span>{photo.metadata.camera}</span>
                  {photo.metadata.date_taken && photo.metadata.date_taken !== 'Unknown' && (
                    <span>{new Date(photo.metadata.date_taken).toLocaleDateString()}</span>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default PhotoGrid;
