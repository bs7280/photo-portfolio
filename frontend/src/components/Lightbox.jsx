import { useEffect } from 'react';
import { useEditMode } from '../context/EditModeContext';
import './Lightbox.css';

const Lightbox = ({ photo, onClose, onNext, onPrev }) => {
  const { editMode } = useEditMode();
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowRight') onNext();
      if (e.key === 'ArrowLeft') onPrev();
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose, onNext, onPrev]);

  if (!photo) return null;

  const { metadata } = photo;

  return (
    <div className="lightbox-overlay" onClick={onClose}>
      <div className="lightbox-content" onClick={(e) => e.stopPropagation()}>
        <button className="lightbox-close" onClick={onClose}>
          ✕
        </button>

        <button className="lightbox-nav lightbox-prev" onClick={onPrev}>
          ‹
        </button>

        <div className="lightbox-image-container">
          <img src={photo.url} alt={photo.filename} />
        </div>

        <button className="lightbox-nav lightbox-next" onClick={onNext}>
          ›
        </button>

        <div className="lightbox-info">
          <h3>{photo.custom_title || photo.filename}</h3>

          {photo.description && (
            <p className="photo-description">{photo.description}</p>
          )}

          {photo.tags && photo.tags.length > 0 && (
            <div className="photo-tags">
              {photo.tags.map(tag => (
                <span key={tag} className="photo-tag">{tag}</span>
              ))}
            </div>
          )}

          {!photo.published && editMode && (
            <div className="unpublished-badge">Unpublished</div>
          )}

          <div className="metadata-grid">
            {metadata.camera && metadata.camera !== 'Unknown' && (
              <div className="metadata-item">
                <span className="label">Camera:</span>
                <span className="value">{metadata.camera}</span>
              </div>
            )}
            {metadata.lens && metadata.lens !== 'Unknown' && (
              <div className="metadata-item">
                <span className="label">Lens:</span>
                <span className="value">{metadata.lens}</span>
              </div>
            )}
            {metadata.iso && metadata.iso !== 'Unknown' && (
              <div className="metadata-item">
                <span className="label">ISO:</span>
                <span className="value">{metadata.iso}</span>
              </div>
            )}
            {metadata.aperture && metadata.aperture !== 'Unknown' && (
              <div className="metadata-item">
                <span className="label">Aperture:</span>
                <span className="value">f/{metadata.aperture}</span>
              </div>
            )}
            {metadata.shutter_speed && metadata.shutter_speed !== 'Unknown' && (
              <div className="metadata-item">
                <span className="label">Shutter:</span>
                <span className="value">{metadata.shutter_speed}s</span>
              </div>
            )}
            {metadata.date_taken && metadata.date_taken !== 'Unknown' && (
              <div className="metadata-item">
                <span className="label">Date:</span>
                <span className="value">{new Date(metadata.date_taken).toLocaleDateString()}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Lightbox;
