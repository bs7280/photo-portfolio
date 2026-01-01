import { useState } from 'react';
import { deployToR2 } from '../api/client';
import './DeployButton.css';

export default function DeployButton() {
  const [deploying, setDeploying] = useState(false);
  const [result, setResult] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  const handleDeploy = async () => {
    if (!confirm('Deploy all published photos to R2? This will upload new photos and remove unpublished ones from the bucket.')) {
      return;
    }

    setDeploying(true);
    setResult(null);

    try {
      const response = await deployToR2();
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
      console.error('Deploy error:', error);
      setResult({
        success: false,
        error: error.response?.data?.error || error.message || 'Failed to deploy'
      });
      setShowDetails(true);
    } finally {
      setDeploying(false);
    }
  };

  return (
    <div className="deploy-button-container">
      <button
        onClick={handleDeploy}
        disabled={deploying}
        className="btn-deploy"
        title="Deploy published photos to R2 bucket"
      >
        {deploying ? '🚀 Deploying...' : '🚀 Deploy to R2'}
      </button>

      {result && showDetails && (
        <div className={`deploy-result ${result.success ? 'success' : 'error'}`}>
          <div className="deploy-result-header">
            <h4>{result.success ? '✓ Deploy Complete' : '✗ Deploy Failed'}</h4>
            <button onClick={() => setShowDetails(false)} className="close-btn">×</button>
          </div>

          {result.success ? (
            <div className="deploy-stats">
              {result.thumbnails_generated > 0 && (
                <div className="stat">
                  <span className="stat-label">Thumbnails Generated:</span>
                  <span className="stat-value">{result.thumbnails_generated}</span>
                </div>
              )}
              <div className="stat">
                <span className="stat-label">Uploaded:</span>
                <span className="stat-value">{result.uploaded}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Deleted:</span>
                <span className="stat-value">{result.deleted}</span>
              </div>

              {result.uploaded_files && result.uploaded_files.length > 0 && (
                <details className="file-list">
                  <summary>Uploaded files ({result.uploaded_files.length})</summary>
                  <ul>
                    {result.uploaded_files.map(file => (
                      <li key={file}>{file}</li>
                    ))}
                  </ul>
                </details>
              )}

              {result.deleted_files && result.deleted_files.length > 0 && (
                <details className="file-list">
                  <summary>Deleted files ({result.deleted_files.length})</summary>
                  <ul>
                    {result.deleted_files.map(file => (
                      <li key={file}>{file}</li>
                    ))}
                  </ul>
                </details>
              )}

              {result.warnings && result.warnings.length > 0 && (
                <details className="file-list">
                  <summary>⚠️ Warnings ({result.warnings.length})</summary>
                  <ul>
                    {result.warnings.map((warning, i) => (
                      <li key={i} style={{color: '#856404'}}>{warning}</li>
                    ))}
                  </ul>
                </details>
              )}

              {result.errors && result.errors.length > 0 && (
                <details className="error-list">
                  <summary>Errors ({result.errors.length})</summary>
                  <ul>
                    {result.errors.map((error, i) => (
                      <li key={i}>{error}</li>
                    ))}
                  </ul>
                </details>
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
