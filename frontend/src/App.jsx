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
      <header className="header">
        <div>
          <h1>{t.app.title}</h1>
          <p>{t.app.subtitle}</p>
          {modelInfo && (
            <p style={{ fontSize: 12, opacity: 0.7, marginTop: 4 }}>
              {modelInfo.type.toUpperCase()} | {modelInfo.num_classes} classes | {modelInfo.input_size}px
            </p>
          )}
        </div>
        <LanguageSwitch lang={lang} onSwitch={setLang} t={t} />
      </header>

      <div className="status-bar">
        <div className={`status-dot ${modelReady ? '' : 'loading'}`} />
        <span>{modelReady ? t.status.ready : t.status.loading}</span>
        {processing && <span style={{ marginLeft: 'auto', fontSize: 14 }}>{t.status.processing}</span>}
      </div>

      <div className="main-grid">
        <div>
          <UploadZone onDetection={handleDetection} t={t} />
          <div style={{ marginTop: 20 }}>
            <CameraFeed 
              onDetection={handleFrameDetection} 
              t={t} 
              confThreshold={confThreshold}
            />
          </div>
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
      </div>

      <InstallPrompt />
    </div>
  );
}

export default App;
