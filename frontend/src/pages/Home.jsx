import { useState, useEffect } from 'react';
import { getPhotos, getAlbums } from '../api/client';
import { useEditMode } from '../context/EditModeContext';
import PhotoGrid from '../components/PhotoGrid';
import Lightbox from '../components/Lightbox';
import BulkActionsBar from '../components/BulkActionsBar';
import './Home.css';

const Home = () => {
  const { editMode } = useEditMode();
  const [photos, setPhotos] = useState([]);
  const [albums, setAlbums] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPhoto, setSelectedPhoto] = useState(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [selectedPhotos, setSelectedPhotos] = useState([]);

  useEffect(() => {
    loadPhotos();
    if (editMode) {
      loadAlbums();
    }
  }, [editMode]);

  const loadPhotos = async () => {
    try {
      const data = await getPhotos();
      setPhotos(data);
    } catch (error) {
      console.error('Error loading photos:', error);
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
    loadPhotos();
    handleClearSelection();
  };

  if (loading) {
    return <div className="loading">Loading photos...</div>;
  }

  return (
    <div className="home">
      <header className="header">
        <h1>Photography Portfolio</h1>
        <p>{photos.length} photos</p>
      </header>

      {editMode && selectedPhotos.length > 0 && (
        <BulkActionsBar
          selectedPhotos={selectedPhotos}
          totalPhotos={photos.length}
          albums={albums}
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

export default Home;
