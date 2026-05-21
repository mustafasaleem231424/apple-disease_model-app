import { exportCSV, exportJSON } from '../services/api';
import { getDiseaseClass, formatConfidence } from '../utils/helpers';

function ResultsPanel({ detections, annotatedImage, t, onClear, processing, error, confThreshold, onConfChange, inferenceTime, imageSize }) {
  const hasDetections = detections && detections.length > 0;

  const getDiseaseLabel = (className) => {
    return t.diseases[className] || className;
  };

  const getDiseaseDesc = (className) => {
    const descs = t.descriptions || {};
    return descs[className] || '';
  };

  const diseaseCounts = {};
  detections.forEach(d => {
    diseaseCounts[d.class_name] = (diseaseCounts[d.class_name] || 0) + 1;
  });

  return (
    <div className="card results-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0, padding: 0, border: 'none' }}>{t.results.title}</h2>
        {hasDetections && (
          <span style={{
            background: 'var(--green-medium)',
            color: 'white',
            padding: '4px 12px',
            borderRadius: 'var(--radius-xl)',
            fontSize: 14,
            fontWeight: 600
          }}>
            {detections.length}
          </span>
        )}
      </div>

      {processing && (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <div className="spinner" style={{ margin: '0 auto 12px' }} />
          <p style={{ color: 'var(--gray-600)' }}>{t.status.processing}</p>
        </div>
      )}

      {error && !processing && (
        <div style={{ background: 'var(--red-light)', color: 'var(--red)', padding: 16, borderRadius: 'var(--radius)', marginBottom: 16, fontSize: 14 }}>
          {error}
        </div>
      )}

      {!processing && !error && hasDetections && (
        <>
          {imageSize && (
            <p style={{ marginBottom: 8, color: 'var(--gray-500)', fontSize: 13 }}>
              Image: {imageSize.width}x{imageSize.height} | {inferenceTime}ms
            </p>
          )}
          
          <div style={{ marginBottom: 12, padding: '8px 12px', background: 'var(--green-pale)', borderRadius: 'var(--radius)', fontSize: 13 }}>
            <strong>Summary:</strong> {Object.entries(diseaseCounts).map(([cls, count]) => (
              <span key={cls} style={{ marginLeft: 8 }}>
                {getDiseaseLabel(cls)}: {count}
              </span>
            ))}
          </div>

          <div className="detection-list">
            {detections.map((det, i) => (
              <div key={i} className={`detection-item ${getDiseaseClass(det.class_name)}`}>
                <div className="detection-info">
                  <div className="detection-name">{getDiseaseLabel(det.class_name)}</div>
                  {getDiseaseDesc(det.class_name) && (
                    <div className="detection-desc">{getDiseaseDesc(det.class_name)}</div>
                  )}
                  <div className="confidence-bar">
                    <div
                      className="confidence-fill"
                      style={{ width: `${det.confidence * 100}%` }}
                    />
                  </div>
                </div>
                <div className="detection-confidence">
                  {formatConfidence(det.confidence)}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {!processing && !error && !hasDetections && (
        <div className="no-detections">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: '0 auto 12px', opacity: 0.5 }}>
            <circle cx="12" cy="12" r="10" />
            <path d="M8 15s1.5 2 4 2 4-2 4-2" />
            <line x1="9" y1="9" x2="9.01" y2="9" />
            <line x1="15" y1="9" x2="15.01" y2="9" />
          </svg>
          <p>{t.results.noDetections}</p>
        </div>
      )}

      {annotatedImage && !processing && (
        <div className="preview-container" style={{ marginTop: 16 }}>
          <img src={`data:image/jpeg;base64,${annotatedImage}`} alt="Detection Result" loading="lazy" />
        </div>
      )}

      {!processing && hasDetections && (
        <>
          <div style={{ marginTop: 16, padding: 12, background: 'var(--gray-50)', borderRadius: 'var(--radius)' }}>
            <label style={{ fontSize: 13, color: 'var(--gray-600)', display: 'block', marginBottom: 8 }}>
              Confidence Threshold: {(confThreshold * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="5"
              max="95"
              value={confThreshold * 100}
              onChange={(e) => onConfChange(parseInt(e.target.value) / 100)}
              style={{ width: '100%', accentColor: 'var(--green-medium)' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--gray-400)' }}>
              <span>5%</span>
              <span>50%</span>
              <span>95%</span>
            </div>
          </div>

          <div className="export-buttons">
            <button className="export-btn" onClick={() => exportCSV()}>{t.results.exportCSV}</button>
            <button className="export-btn" onClick={() => exportJSON()}>{t.results.exportJSON}</button>
            <button className="export-btn danger" onClick={onClear}>{t.results.clearHistory}</button>
          </div>
        </>
      )}
    </div>
  );
}

export default ResultsPanel;
