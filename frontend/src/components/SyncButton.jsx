import { useState } from 'react';
import { syncDatabase } from '../api/client';
import './SyncButton.css';

export default function SyncButton() {
  const [syncing, setSyncing] = useState(false);
  const [result, setResult] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  const handleSync = async () => {
    if (!confirm('Sync database with filesystem? This will add new photos and update EXIF data.')) {
      return;
    }

    setSyncing(true);
    setResult(null);

    try {
      const response = await syncDatabase();
      setResult(response);
      setShowDetails(true);

      // Auto-hide success message after 5 seconds
      if (response.success) {
        setTimeout(() => {
          setShowDetails(false);
          setResult(null);
        }, 5000);
      }
    } catch (error) {
      console.error('Sync error:', error);
      setResult({
        success: false,
        error: error.response?.data?.error || error.message || 'Failed to sync'
      });
      setShowDetails(true);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="sync-button-container">
      <button
        onClick={handleSync}
        disabled={syncing}
        className="btn-sync"
        title="Sync database with filesystem (add new photos, update EXIF)"
      >
        {syncing ? '🔄 Syncing...' : '🔄 Sync Database'}
      </button>

      {result && showDetails && (
        <div className={`sync-result ${result.success ? 'success' : 'error'}`}>
          <div className="sync-result-header">
            <h4>{result.success ? '✓ Sync Complete' : '✗ Sync Failed'}</h4>
            <button onClick={() => setShowDetails(false)} className="close-btn">×</button>
          </div>

          {result.success ? (
            <div className="sync-stats">
              <div className="stat">
                <span className="stat-label">Added:</span>
                <span className="stat-value">{result.added || 0}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Removed:</span>
                <span className="stat-value">{result.removed || 0}</span>
              </div>
              {result.message && (
                <div className="sync-message">{result.message}</div>
              )}
            </div>
          ) : (
            <div className="error-message">
              {result.error || 'An unknown error occurred'}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
