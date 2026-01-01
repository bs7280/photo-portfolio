import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getAlbumPhotos, getAlbums } from '../api/client';
import { useEditMode } from '../context/EditModeContext';
import PhotoGrid from '../components/PhotoGrid';
import Lightbox from '../components/Lightbox';
import BulkActionsBar from '../components/BulkActionsBar';
import { DeleteAlbumButton } from '../components/AlbumEditControls';
import './AlbumDetail.css';

const AlbumDetail = () => {
  const { albumId } = useParams();
  const navigate = useNavigate();
  const { editMode } = useEditMode();
  const [photos, setPhotos] = useState([]);
  const [albums, setAlbums] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPhoto, setSelectedPhoto] = useState(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [selectedPhotos, setSelectedPhotos] = useState([]);

  useEffect(() => {
    loadAlbumPhotos();
    if (editMode) {
      loadAlbums();
    }
  }, [albumId, editMode]);

  const loadAlbumPhotos = async () => {
    try {
      const data = await getAlbumPhotos(albumId);
      setPhotos(data);
    } catch (error) {
      console.error('Error loading album photos:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAlbums = async () => {
    try {
      const data = await getAlbums();
      setAlbums(data);
    } catch (error) {
      console.error('Error loading albums:', error);
    }
  };

  const handlePhotoClick = (photo) => {
    const index = photos.findIndex((p) => p.id === photo.id);
    setSelectedPhoto(photo);
    setSelectedIndex(index);
  };

  const handleNext = () => {
    const nextIndex = (selectedIndex + 1) % photos.length;
    setSelectedIndex(nextIndex);
    setSelectedPhoto(photos[nextIndex]);
  };

  const handlePrev = () => {
    const prevIndex = (selectedIndex - 1 + photos.length) % photos.length;
    setSelectedIndex(prevIndex);
    setSelectedPhoto(photos[prevIndex]);
  };

  const handleToggleSelect = (photoId) => {
    setSelectedPhotos(prev =>
      prev.includes(photoId)
        ? prev.filter(id => id !== photoId)
        : [...prev, photoId]
    );
  };

  const handleSelectAll = () => {
    setSelectedPhotos(photos.map(p => p.id));
  };

  const handleClearSelection = () => {
    setSelectedPhotos([]);
  };

  const handleActionComplete = () => {
    loadAlbumPhotos();
    handleClearSelection();
  };

  const handleAlbumDeleted = () => {
    navigate('/albums');
  };

  if (loading) {
    return <div className="loading">Loading album...</div>;
  }

  return (
    <div className="album-detail">
      <header className="header">
        <Link to="/albums" className="back-link">← Back to Albums</Link>
        <div className="header-content">
          <div>
            <h1>{albumId}</h1>
            <p>{photos.length} photos</p>
          </div>
          {editMode && (
            <DeleteAlbumButton
              albumId={albumId}
              albumName={albumId}
              onAlbumDeleted={handleAlbumDeleted}
            />
          )}
        </div>
      </header>

      {editMode && selectedPhotos.length > 0 && (
        <BulkActionsBar
          selectedPhotos={selectedPhotos}
          totalPhotos={photos.length}
          albums={albums.filter(a => a.id !== albumId)}
          onSelectAll={handleSelectAll}
          onClearSelection={handleClearSelection}
          onActionComplete={handleActionComplete}
        />
      )}

      <PhotoGrid
        photos={photos}
        onPhotoClick={handlePhotoClick}
        selectedPhotos={selectedPhotos}
        onToggleSelect={handleToggleSelect}
      />

      {selectedPhoto && (
        <Lightbox
          photo={selectedPhoto}
          onClose={() => setSelectedPhoto(null)}
          onNext={handleNext}
          onPrev={handlePrev}
        />
      )}
    </div>
  );
};

export default AlbumDetail;
