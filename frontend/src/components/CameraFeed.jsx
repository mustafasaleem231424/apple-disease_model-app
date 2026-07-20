import { useState, useRef, useCallback, useEffect } from 'react';
import { useCamera } from '../hooks/useCamera';
import { drawDetections, formatConfidence, getDiseaseColor } from '../utils/helpers';

function CameraFeed({ onDetection, t, confThreshold }) {
  const [scanning, setScanning] = useState(false);
  const [scanLog, setScanLog] = useState([]);
  const [detectionCount, setDetectionCount] = useState(0);
  const [fps, setFps] = useState(0);
  const [scanInterval, setScanInterval] = useState(400); // Default real-time: 400ms (2.5 FPS)
  const [selectedCamera, setSelectedCamera] = useState('');
  
  const canvasRef = useRef(null);
  const intervalRef = useRef(null);
  const frameCountRef = useRef(0);
  const lastFpsTimeRef = useRef(Date.now());
  
  const { 
    videoRef, 
    active, 
    error, 
    devices, 
    start, 
    stop, 
    captureBlob 
  } = useCamera({ facingMode: 'environment' });

  // Update selected camera source on load or change
  useEffect(() => {
    if (devices.length > 0 && !selectedCamera) {
      // Prioritize rear camera for agricultural scanning
      const backCamera = devices.find(d => d.label.toLowerCase().includes('back') || d.label.toLowerCase().includes('environment'));
      setSelectedCamera(backCamera ? backCamera.deviceId : devices[0].deviceId);
    }
  }, [devices, selectedCamera]);

  const processFrame = useCallback(async () => {
    const blob = await captureBlob(0.7);
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
          return updated.slice(0, 50); // Keep last 50 entries
        });
      }
    }
  }, [captureBlob, onDetection, confThreshold]);

  const startScanning = useCallback(async () => {
    await start(selectedCamera);
    setScanning(true);
    setScanLog([]);
    setDetectionCount(0);
    setFps(0);
    frameCountRef.current = 0;
    lastFpsTimeRef.current = Date.now();
  }, [start, selectedCamera]);

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

  // Restart scan interval when scanning state or scanInterval changes
  useEffect(() => {
    if (scanning && active) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = setInterval(async () => {
        try {
          await processFrame();
        } catch (err) {
          console.error('Frame processing error:', err);
        }
      }, scanInterval);
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [scanning, active, scanInterval, processFrame]);

  const handleCameraChange = async (e) => {
    const newDeviceId = e.target.value;
    setSelectedCamera(newDeviceId);
    if (active) {
      // Hot-swap camera feed
      await start(newDeviceId);
    }
  };

  const diseaseSummary = {};
  scanLog.forEach(d => {
    diseaseSummary[d.class_name] = (diseaseSummary[d.class_name] || 0) + 1;
  });

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
        <h2 style={{ margin: 0, padding: 0, border: 'none' }}>{t.camera.title}</h2>
        
        {scanning && active && (
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <span style={{ fontSize: 13, color: 'var(--mint)', fontWeight: 700, letterSpacing: '0.02em' }}>
              {fps} FPS
            </span>
            <span className="live-scanning-badge animate-pulse">
              LIVE CHECKING ACTIVE
            </span>
          </div>
        )}
      </div>

      {/* Camera Selection dropdown (for multiple back/front cameras on phone) */}
      {devices.length > 1 && (
        <div style={{ marginBottom: 12 }}>
          <label style={{ fontSize: 12, color: 'var(--text-secondary)', display: 'block', marginBottom: 4, fontWeight: 600 }}>
            SELECT CAMERA SOURCE:
          </label>
          <select 
            value={selectedCamera} 
            onChange={handleCameraChange}
            style={{
              width: '100%',
              padding: '8px 12px',
              background: 'rgba(0,0,0,0.4)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              outline: 'none',
              fontSize: '13px',
              fontFamily: 'Plus Jakarta Sans',
              cursor: 'pointer'
            }}
          >
            {devices.map(device => (
              <option key={device.deviceId} value={device.deviceId}>
                {device.label || `Camera ${devices.indexOf(device) + 1}`}
              </option>
            ))}
          </select>
        </div>
      )}
      
      <div className="camera-container">
        <video ref={videoRef} autoPlay playsInline muted style={{ display: active ? 'block' : 'none' }} />
        <canvas ref={canvasRef} className="camera-overlay" style={{ width: '100%', height: '100%' }} />
        
        {!active && (
          <div style={{ padding: '60px 20px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: '0 auto 16px', opacity: 0.4 }}>
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
              <circle cx="12" cy="13" r="4" />
            </svg>
            <h4 className="font-outfit" style={{ color: 'var(--text-primary)', fontSize: '1.1rem', marginBottom: 6 }}>Real-Time Diagnostics Feed</h4>
            <p style={{ fontSize: '13px', maxWidth: '320px', margin: '0 auto' }}>Tap the start button below to launch the video feed for real-time orchard disease scanning.</p>
          </div>
        )}
        
        {scanning && active && (
          <div style={{
            position: 'absolute',
            bottom: 12,
            left: 12,
            background: 'rgba(5, 8, 6, 0.85)',
            border: '1px solid var(--border-color)',
            color: 'var(--white)',
            padding: '6px 12px',
            borderRadius: 'var(--radius-sm)',
            fontSize: 12,
            fontFamily: 'Outfit',
            zIndex: 6,
            backdropFilter: 'blur(4px)'
          }}>
            {detectionCount} Frames Checked | {Object.keys(diseaseSummary).length} Pathology Types
          </div>
        )}
      </div>

      {/* Real-time speed adjustments */}
      {active && (
        <div className="slider-control-card" style={{ marginTop: 12, padding: '10px 14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, fontWeight: 600 }}>
            <span>Scan Frequency:</span>
            <span style={{ color: 'var(--mint)' }}>{Math.round(1000 / scanInterval)} Scans / Sec</span>
          </div>
          <input 
            type="range"
            min="200"
            max="2000"
            step="100"
            value={scanInterval}
            onChange={(e) => setScanInterval(parseInt(e.target.value))}
            style={{ width: '100%', margin: '8px 0 4px', accentColor: 'var(--emerald)' }}
          />
          <div className="slider-labels">
            <span>5 Scans/Sec (FAST)</span>
            <span>0.5 Scans/Sec (CPU CONSERVATIVE)</span>
          </div>
        </div>
      )}
      
      <div className="camera-controls">
        {!active ? (
          <button className="camera-btn start" onClick={startScanning}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            START REAL-TIME SCAN
          </button>
        ) : (
          <button className="camera-btn stop" onClick={stopScanning}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="6" width="12" height="12" />
            </svg>
            STOP CAMERA SCAN
          </button>
        )}
      </div>
      
      {error && <p style={{ color: 'var(--red)', marginTop: 8, fontSize: 14, fontWeight: 600 }}>{error}</p>}
      
      {scanning && scanLog.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <h3 className="font-outfit" style={{ fontSize: 13, color: 'var(--white)', marginBottom: 8, letterSpacing: '0.05em' }}>
            ACCUMULATED FIELD SCAN LOG:
          </h3>
          
          {Object.keys(diseaseSummary).length > 0 && (
            <div style={{
              display: 'flex',
              gap: 8,
              flexWrap: 'wrap',
              marginBottom: 12
            }}>
              {Object.entries(diseaseSummary).map(([cls, count]) => (
                <span key={cls} className="summary-pill" style={{
                  borderColor: cls === 'healthy_apple' ? 'var(--emerald)' : 'var(--orange)',
                  background: cls === 'healthy_apple' ? 'rgba(16,185,129,0.1)' : 'rgba(249,115,22,0.1)',
                }}>
                  <span className="summary-pill-name">{cls.replace(/_/g, ' ').toUpperCase()}</span>
                  <span className="summary-pill-count" style={{
                    background: cls === 'healthy_apple' ? 'var(--emerald)' : 'var(--orange)',
                    color: '#000'
                  }}>{count}</span>
                </span>
              ))}
            </div>
          )}
          
          <div style={{
            maxHeight: 180,
            overflowY: 'auto',
            fontSize: 12,
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(0,0,0,0.2)'
          }}>
            {scanLog.slice(0, 20).map((det) => (
              <div key={det.id} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 12px',
                borderBottom: '1px solid var(--border-color)',
                borderLeft: `4px solid ${det.class_name === 'healthy_apple' ? 'var(--emerald)' : 'var(--orange)'}`
              }}>
                <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{det.class_name.replace(/_/g, ' ').toUpperCase()}</span>
                <span style={{ color: 'var(--mint)', fontWeight: 800 }}>{formatConfidence(det.confidence)}</span>
                <span style={{ color: 'var(--text-muted)' }}>{det.timestamp}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default CameraFeed;
