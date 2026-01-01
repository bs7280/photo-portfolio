import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getAlbums } from '../api/client';
import { useEditMode } from '../context/EditModeContext';
import { CreateAlbumButton } from '../components/AlbumEditControls';
import './Albums.css';

const Albums = () => {
  const { editMode } = useEditMode();
  const [albums, setAlbums] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAlbums();
  }, []);

  const loadAlbums = async () => {
    try {
      const data = await getAlbums();
      setAlbums(data);
    } catch (error) {
      console.error('Error loading albums:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading albums...</div>;
  }

  return (
    <div className="albums">
      <header className="header">
        <div className="header-content">
          <div>
            <h1>Albums</h1>
            <p>{albums.length} albums</p>
          </div>
          {editMode && (
            <CreateAlbumButton onAlbumCreated={loadAlbums} />
          )}
        </div>
      </header>

      <div className="albums-grid">
        {albums.map((album) => (
          <Link key={album.id} to={`/albums/${album.id}`} className="album-card">
            <div className="album-cover">
              {album.cover_photo && (
                <img src={album.cover_photo} alt={album.name} />
              )}
            </div>
            <div className="album-info">
              <h3>{album.name}</h3>
              <p>{album.photo_count} photos</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default Albums;
