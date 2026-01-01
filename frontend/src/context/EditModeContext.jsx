import { createContext, useContext, useState, useEffect } from 'react';
import { getConfig } from '../api/client';

const EditModeContext = createContext();

export function EditModeProvider({ children }) {
  const [editMode, setEditMode] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const config = await getConfig();
      setEditMode(config.edit_mode || false);
      setError(null);
    } catch (err) {
      console.error('Error loading config:', err);
      setEditMode(false);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const value = {
    editMode,
    loading,
    error,
    refresh: loadConfig
  };

  return (
    <EditModeContext.Provider value={value}>
      {children}
    </EditModeContext.Provider>
  );
}

export function useEditMode() {
  const context = useContext(EditModeContext);
  if (context === undefined) {
    throw new Error('useEditMode must be used within an EditModeProvider');
  }
  return context;
}
