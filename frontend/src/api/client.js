import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL;

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getPhotos = async () => {
  const response = await apiClient.get('/photos');
  return response.data;
};

export const getAlbums = async () => {
  const response = await apiClient.get('/albums');
  return response.data;
};

export const getAlbumPhotos = async (albumId) => {
  const response = await apiClient.get(`/albums/${albumId}/photos`);
  return response.data;
};

// Configuration
export const getConfig = async () => {
  const response = await apiClient.get('/config');
  return response.data;
};

// Photo edit operations
export const updatePhotoMetadata = async (photoId, metadata) => {
  const response = await apiClient.post(`/photos/${photoId}/metadata`, metadata);
  return response.data;
};

export const movePhoto = async (photoId, targetAlbum) => {
  const response = await apiClient.post(`/photos/${photoId}/move`, { album: targetAlbum });
  return response.data;
};

export const deletePhoto = async (photoId) => {
  const response = await apiClient.delete(`/photos/${photoId}`);
  return response.data;
};

// Album edit operations
export const createAlbum = async (name) => {
  const response = await apiClient.post('/albums', { name });
  return response.data;
};

export const updateAlbum = async (albumId, metadata) => {
  const response = await apiClient.put(`/albums/${albumId}`, metadata);
  return response.data;
};

export const deleteAlbum = async (albumId, deletePhotos = false) => {
  const response = await apiClient.delete(`/albums/${albumId}`, {
    data: { delete_photos: deletePhotos }
  });
  return response.data;
};

// Database sync
export const syncDatabase = async () => {
  const response = await apiClient.post('/sync');
  return response.data;
};

// Deploy to R2
export const deployToR2 = async () => {
  const response = await apiClient.post('/deploy');
  return response.data;
};

export default apiClient;
