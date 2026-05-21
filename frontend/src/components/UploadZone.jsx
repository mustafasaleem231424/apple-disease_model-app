import { useState, useRef, useCallback, useEffect } from 'react';
import { validateFile } from '../utils/helpers';

function UploadZone({ onDetection, t, maxSizeMB = 16, onImageSelect }) {
  const [dragOver, setDragOver] = useState(false);
  const [preview, setPreview] = useState(null);
  const fileInputRef = useRef(null);

  const handleFile = useCallback(async (file) => {
    const error = validateFile(file, maxSizeMB);
    if (error) {
      console.error(error);
      return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target.result);
      if (onImageSelect) onImageSelect(e.target.result);
    };
    reader.readAsDataURL(file);
    
    onDetection(file);
  }, [onDetection, maxSizeMB, onImageSelect]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  }, [handleFile]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragOver(false);
  }, []);

  const handleInputChange = useCallback((e) => {
    const file = e.target.files[0];
    handleFile(file);
    e.target.value = '';
  }, [handleFile]);

  const handleClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  return (
    <div className="card">
      <h2>{t.upload.title}</h2>
      
      {preview && (
        <div className="preview-container" style={{ marginBottom: 16 }}>
          <img src={preview} alt="Preview" style={{ maxHeight: 200, objectFit: 'contain' }} />
          <button 
            onClick={(e) => { e.stopPropagation(); setPreview(null); if (onImageSelect) onImageSelect(null); }}
            style={{ position: 'absolute', top: 8, right: 8, background: 'rgba(0,0,0,0.6)', color: 'white', border: 'none', borderRadius: '50%', width: 28, height: 28, cursor: 'pointer', fontSize: 16 }}
          >
            x
          </button>
        </div>
      )}
      
      <div
        className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleClick}
        role="button"
        tabIndex={0}
        aria-label={t.upload.title}
      >
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ margin: '0 auto 12px', opacity: 0.6 }}>
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        <p>{t.upload.drag}</p>
        <p>{t.upload.or}</p>
        <button className="upload-btn" onClick={(e) => { e.stopPropagation(); handleClick(); }}>
          {t.upload.browse}
        </button>
        <p style={{ fontSize: 12, marginTop: 12, opacity: 0.7 }}>{t.upload.supported}</p>
      </div>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        style={{ display: 'none' }}
        onChange={handleInputChange}
      />
    </div>
  );
}

export default UploadZone;
