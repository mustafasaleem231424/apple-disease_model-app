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

  const getSeverityLevel = (className) => {
    switch (className) {
      case 'healthy_apple':
        return { label: 'HEALTHY', color: 'var(--emerald)', bg: 'rgba(16, 185, 129, 0.1)' };
      case 'powdery_mildew':
        return { label: 'MODERATE SEVERITY', color: 'var(--yellow)', bg: 'rgba(245, 158, 11, 0.1)' };
      case 'apple_scab':
      case 'cedar_apple_rust':
      case 'black_rot':
        return { label: 'HIGH SEVERITY', color: 'var(--red)', bg: 'rgba(239, 68, 68, 0.1)' };
      default:
        return { label: 'ATTENTION', color: 'var(--orange)', bg: 'rgba(249, 115, 22, 0.1)' };
    }
  };

  const diseaseCounts = {};
  let containsDiseases = false;
  
  detections.forEach(d => {
    diseaseCounts[d.class_name] = (diseaseCounts[d.class_name] || 0) + 1;
    if (d.class_name !== 'healthy_apple' && d.class_name !== 'other') {
      containsDiseases = true;
    }
  });

  return (
    <div className="card results-panel animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ margin: 0, padding: 0, border: 'none' }}>{t.results.title}</h2>
        {hasDetections && (
          <span className="results-count-badge">
            {detections.length} Total
          </span>
        )}
      </div>

      {processing && (
        <div className="results-loader">
          <div className="spinner" />
          <p>{t.status.processing}</p>
        </div>
      )}

      {error && !processing && (
        <div className="error-banner">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: 8, flexShrink: 0 }}>
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {!processing && !error && hasDetections && (
        <>
          {/* Psychologically-Driven Diagnostic Banner */}
          {containsDiseases ? (
            <div className="diagnostic-banner alert">
              <div className="diagnostic-banner-icon">⚠️</div>
              <div>
                <h4 className="font-outfit">Active Pathogens Detected</h4>
                <p>Treatment protocols or targeted spraying are recommended to prevent orchard contamination.</p>
              </div>
            </div>
          ) : (
            <div className="diagnostic-banner success">
              <div className="diagnostic-banner-icon">🛡️</div>
              <div>
                <h4 className="font-outfit">Foliage Appears Healthy</h4>
                <p>No actionable disease signatures were detected on the leaf surfaces.</p>
              </div>
            </div>
          )}

          {imageSize && (
            <div className="metric-row">
              <span>Resolution: {imageSize.width} × {imageSize.height}</span>
              <span>Latency: {inferenceTime}ms</span>
            </div>
          )}
          
          <div className="summary-pills-container">
            {Object.entries(diseaseCounts).map(([cls, count]) => {
              const severity = getSeverityLevel(cls);
              return (
                <div key={cls} className="summary-pill" style={{ borderColor: severity.color, background: severity.bg }}>
                  <span className="summary-pill-name">{getDiseaseLabel(cls)}</span>
                  <span className="summary-pill-count" style={{ background: severity.color }}>{count}</span>
                </div>
              );
            })}
          </div>

          <div className="detection-list">
            {detections.map((det, i) => {
              const severity = getSeverityLevel(det.class_name);
              return (
                <div key={i} className={`detection-item ${getDiseaseClass(det.class_name)}`}>
                  <div className="detection-info">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      <span className="detection-name">{getDiseaseLabel(det.class_name)}</span>
                      <span className="severity-badge" style={{ color: severity.color, background: severity.bg, borderColor: severity.color }}>
                        {severity.label}
                      </span>
                    </div>
                    {getDiseaseDesc(det.class_name) && (
                      <div className="detection-desc">{getDiseaseDesc(det.class_name)}</div>
                    )}
                    <div className="confidence-bar">
                      <div
                        className="confidence-fill"
                        style={{ width: `${det.confidence * 100}%`, background: severity.color }}
                      />
                    </div>
                  </div>
                  <div className="detection-confidence" style={{ color: severity.color }}>
                    {formatConfidence(det.confidence)}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {!processing && !error && !hasDetections && (
        <div className="no-detections">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ opacity: 0.3, marginBottom: 16 }}>
            <circle cx="12" cy="12" r="10" />
            <path d="M8 15s1.5 2 4 2 4-2 4-2" />
            <line x1="9" y1="9" x2="9.01" y2="9" />
            <line x1="15" y1="9" x2="15.01" y2="9" />
          </svg>
          <p className="font-outfit">{t.results.noDetections}</p>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>Upload an orchard image or launch the live camera feed to start the diagnostic scan.</p>
        </div>
      )}

      {annotatedImage && !processing && (
        <div className="preview-container">
          <div className="preview-tag font-outfit">ANNOTATED SCAN</div>
          <img src={`data:image/jpeg;base64,${annotatedImage}`} alt="Detection Result" loading="lazy" />
        </div>
      )}

      {!processing && hasDetections && (
        <>
          <div className="slider-control-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <label className="font-outfit" style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                Confidence Threshold:
              </label>
              <span className="slider-value font-outfit">{(confThreshold * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="5"
              max="95"
              value={confThreshold * 100}
              onChange={(e) => onConfChange(parseInt(e.target.value) / 100)}
              style={{ width: '100%', accentColor: 'var(--emerald)' }}
            />
            <div className="slider-labels">
              <span>5% (MAX SENSITIVITY)</span>
              <span>50%</span>
              <span>95% (MAX PRECISION)</span>
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
