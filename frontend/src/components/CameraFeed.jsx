import { useState, useRef, useCallback, useEffect } from 'react';
import { useCamera } from '../hooks/useCamera';
import { drawDetections, formatConfidence, getDiseaseColor } from '../utils/helpers';

function CameraFeed({ onDetection, t, confThreshold }) {
  const [scanning, setScanning] = useState(false);
  const [scanLog, setScanLog] = useState([]);
  const [detectionCount, setDetectionCount] = useState(0);
  const [fps, setFps] = useState(0);
  const canvasRef = useRef(null);
  const intervalRef = useRef(null);
  const frameCountRef = useRef(0);
  const lastFpsTimeRef = useRef(Date.now());
  const { videoRef, active, error, start, stop, captureBlob } = useCamera({ facingMode: 'environment' });

  const processFrame = useCallback(async () => {
    const blob = await captureBlob(0.8);
    if (!blob) return;
    
    frameCountRef.current++;
    const now = Date.now();
    if (now - lastFpsTimeRef.current >= 1000) {
      setFps(frameCountRef.current);
      frameCountRef.current = 0;
      lastFpsTimeRef.current = now;
    }
    
    const file = new File([blob], 'frame.jpg', { type: 'image/jpeg' });
    const result = await onDetection(file, confThreshold);
    
    if (result && canvasRef.current && result.detections) {
      const canvas = canvasRef.current;
      canvas.width = result.image_width || 640;
      canvas.height = result.image_height || 480;
      
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      drawDetections(canvas, result.detections, { lineWidth: 3, fontSize: 13 });
      
      if (result.detections.length > 0) {
        setDetectionCount(prev => prev + result.detections.length);
        
        const newDetections = result.detections.map(d => ({
          ...d,
          timestamp: new Date().toLocaleTimeString(),
          id: Date.now() + Math.random()
        }));
        
        setScanLog(prev => {
          const updated = [...newDetections, ...prev];
          return updated.slice(0, 100);
        });
      }
    }
  }, [captureBlob, onDetection, confThreshold]);

  const startScanning = useCallback(async () => {
    await start();
    setScanning(true);
    setScanLog([]);
    setDetectionCount(0);
    setFps(0);
    frameCountRef.current = 0;
    lastFpsTimeRef.current = Date.now();
    
    intervalRef.current = setInterval(async () => {
      try {
        await processFrame();
      } catch (err) {
        console.error('Frame processing error:', err);
      }
    }, 800);
  }, [start, processFrame]);

  const stopScanning = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    stop();
    setScanning(false);
    setFps(0);
    
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    }
  }, [stop]);

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const diseaseSummary = {};
  scanLog.forEach(d => {
    diseaseSummary[d.class_name] = (diseaseSummary[d.class_name] || 0) + 1;
  });

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0, padding: 0, border: 'none' }}>{t.camera.title}</h2>
        {scanning && (
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <span style={{ fontSize: 13, color: 'var(--green-medium)', fontWeight: 600 }}>
              {fps} FPS
            </span>
            <span style={{
              background: 'var(--red)',
              color: 'white',
              padding: '4px 10px',
              borderRadius: 'var(--radius-xl)',
              fontSize: 13,
              fontWeight: 600,
              animation: 'pulse 1.5s ease-in-out infinite'
            }}>
              SCANNING
            </span>
          </div>
        )}
      </div>
      
      <div className="camera-container" style={{ position: 'relative' }}>
        <video ref={videoRef} autoPlay playsInline muted style={{ display: active ? 'block' : 'none' }} />
        <canvas ref={canvasRef} className="camera-overlay" style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }} />
        
        {!active && (
          <div style={{ padding: 60, textAlign: 'center', color: '#999' }}>
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: '0 auto 12px', opacity: 0.5 }}>
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
              <circle cx="12" cy="13" r="4" />
            </svg>
            <p>Point camera at apple trees to scan for diseases</p>
          </div>
        )}
        
        {scanning && (
          <div style={{
            position: 'absolute',
            bottom: 12,
            left: 12,
            background: 'rgba(0,0,0,0.7)',
            color: 'white',
            padding: '6px 12px',
            borderRadius: 'var(--radius)',
            fontSize: 12
          }}>
            {detectionCount} detections | {Object.keys(diseaseSummary).length} disease types
          </div>
        )}
      </div>
      
      <div className="camera-controls">
        {!active ? (
          <button className="camera-btn start" onClick={startScanning}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style={{ marginRight: 6, verticalAlign: 'middle' }}>
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            {t.camera.start}
          </button>
        ) : (
          <button className="camera-btn stop" onClick={stopScanning}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style={{ marginRight: 6, verticalAlign: 'middle' }}>
              <rect x="6" y="6" width="12" height="12" />
            </svg>
            {t.camera.stop}
          </button>
        )}
      </div>
      
      {error && <p style={{ color: '#dc2626', marginTop: 8, fontSize: 14 }}>{error}</p>}
      
      {scanning && scanLog.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <h3 style={{ fontSize: 14, color: 'var(--green-primary)', marginBottom: 8 }}>
            Scan Log ({scanLog.length} detections)
          </h3>
          
          {Object.keys(diseaseSummary).length > 0 && (
            <div style={{
              display: 'flex',
              gap: 8,
              flexWrap: 'wrap',
              marginBottom: 12,
              padding: 10,
              background: 'var(--green-pale)',
              borderRadius: 'var(--radius)'
            }}>
              {Object.entries(diseaseSummary).map(([cls, count]) => (
                <span key={cls} style={{
                  background: getDiseaseColor(cls),
                  color: 'white',
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-xl)',
                  fontSize: 12,
                  fontWeight: 600
                }}>
                  {cls.replace(/_/g, ' ')}: {count}
                </span>
              ))}
            </div>
          )}
          
          <div style={{ maxHeight: 200, overflowY: 'auto', fontSize: 12 }}>
            {scanLog.slice(0, 20).map((det, i) => (
              <div key={det.id} style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '6px 8px',
                borderBottom: '1px solid var(--gray-200)',
                borderLeft: `3px solid ${getDiseaseColor(det.class_name)}`
              }}>
                <span style={{ fontWeight: 600 }}>{det.class_name.replace(/_/g, ' ')}</span>
                <span>{formatConfidence(det.confidence)}</span>
                <span style={{ color: 'var(--gray-500)' }}>{det.timestamp}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default CameraFeed;
