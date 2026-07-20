import { useState, useEffect, useCallback } from 'react';
import UploadZone from './components/UploadZone';
import CameraFeed from './components/CameraFeed';
import ResultsPanel from './components/ResultsPanel';
import LanguageSwitch from './components/LanguageSwitch';
import InstallPrompt from './components/InstallPrompt';
import { useDetection } from './hooks/useDetection';
import { getHealth, getModelInfo } from './services/api';
import en from './i18n/en.json';
import hi from './i18n/hi.json';
import './styles/theme.css';

const translations = { en, hi };

function App() {
  const [lang, setLang] = useState('en');
  const [modelReady, setModelReady] = useState(false);
  const [modelInfo, setModelInfo] = useState(null);
  const [confThreshold, setConfThreshold] = useState(0.25);
  const [imageSize, setImageSize] = useState(null);
  const [inferenceTime, setInferenceTime] = useState(null);
  const [activeTab, setActiveTab] = useState('live'); // 'live' is default, highlighting real-time check
  
  const t = translations[lang];
  
  const {
    detections,
    annotatedImage,
    processing,
    error,
    detectImage,
    processFrame,
    clearHistory,
    reset
  } = useDetection();

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await getHealth();
        setModelReady(health.status === 'healthy');
        if (health.model && health.model.type === 'onnx') {
          try {
            const info = await getModelInfo();
            setModelInfo(info);
          } catch (e) {
            console.warn('Could not fetch model info');
          }
        }
      } catch (err) {
        console.error('Health check failed:', err);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleDetection = useCallback(async (file, conf) => {
    reset();
    try {
      const result = await detectImage(file, conf || confThreshold);
      if (result) {
        setInferenceTime(result.inference_time_ms);
        setImageSize({ width: result.image_width, height: result.image_height });
      }
      return result;
    } catch (err) {
      console.error('Detection failed:', err);
      return null;
    }
  }, [detectImage, confThreshold, reset]);

  const handleFrameDetection = useCallback(async (file, conf) => {
    const result = await processFrame(file, conf || confThreshold);
    if (result) {
      setInferenceTime(result.inference_time_ms);
    }
    return result;
  }, [processFrame, confThreshold]);

  const handleClear = useCallback(async () => {
    await clearHistory();
    reset();
    setImageSize(null);
    setInferenceTime(null);
  }, [clearHistory, reset]);

  return (
    <div className="app-container">
      {/* Premium Hero Banner Section */}
      <section className="hero-banner animate-fade-in">
        <div className="hero-background-wrapper">
          <img src="/dashboard_banner.png" alt="Agricultural Diagnostics Banner" className="hero-bg" />
          <div className="hero-gradient-overlay" />
        </div>
        <div className="hero-content">
          <div className="hero-meta">
            <h1>{t.app.title}</h1>
            <p className="hero-subtitle">{t.app.subtitle}</p>
            {modelInfo && (
              <div className="model-badge-container">
                <span className="model-badge font-outfit">
                  {modelInfo.type.toUpperCase()} MODEL ACTIVE
                </span>
                <span className="model-badge-detail">
                  {modelInfo.num_classes} Classes | {modelInfo.input_size}px Resolution
                </span>
              </div>
            )}
          </div>
          <LanguageSwitch lang={lang} onSwitch={setLang} t={t} />
        </div>
      </section>

      {/* Control Tabs - Psychologically prioritizing Real-Time checker */}
      <div className="tab-navigation-container">
        <button 
          className={`tab-btn font-outfit ${activeTab === 'live' ? 'active' : ''}`}
          onClick={() => { setActiveTab('live'); reset(); }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ marginRight: 8 }}>
            <path d="M23 7l-7 5 7 5V7z" />
            <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
          </svg>
          REAL-TIME SCANNERS
        </button>
        <button 
          className={`tab-btn font-outfit ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => { setActiveTab('upload'); reset(); }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ marginRight: 8 }}>
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <polyline points="21 15 16 10 5 21" />
          </svg>
          STATIC PHOTO ANALYZERS
        </button>
      </div>

      {/* Global Status Banner */}
      <div className="status-container">
        <div className="status-bar">
          <div className={`status-dot ${modelReady ? '' : 'loading'}`} />
          <span>{modelReady ? t.status.ready.toUpperCase() : t.status.loading.toUpperCase()}</span>
          {processing && (
            <div className="status-processing-pill">
              <div className="spinner-mini" />
              <span>{t.status.processing.toUpperCase()}</span>
            </div>
          )}
        </div>
      </div>

      {/* Primary Dashboard Grid */}
      <main className="main-grid">
        <div className="actions-column">
          {activeTab === 'live' ? (
            <div className="animate-fade-in">
              <CameraFeed 
                onDetection={handleFrameDetection} 
                t={t} 
                confThreshold={confThreshold}
              />
            </div>
          ) : (
            <div className="animate-fade-in">
              <UploadZone onDetection={handleDetection} t={t} />
            </div>
          )}
        </div>
        <ResultsPanel
          detections={detections}
          annotatedImage={annotatedImage}
          t={t}
          onClear={handleClear}
          processing={processing}
          error={error}
          confThreshold={confThreshold}
          onConfChange={setConfThreshold}
          inferenceTime={inferenceTime}
          imageSize={imageSize}
        />
      </main>

      <InstallPrompt />
    </div>
  );
}

export default App;
