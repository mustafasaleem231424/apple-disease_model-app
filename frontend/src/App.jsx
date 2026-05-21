import { useState, useEffect, useCallback, useRef } from 'react';
import UploadZone from './components/UploadZone';
import CameraFeed from './components/CameraFeed';
import ResultsPanel from './components/ResultsPanel';
import LanguageSwitch from './components/LanguageSwitch';
import InstallPrompt from './components/InstallPrompt';
import { useDetection } from './hooks/useDetection';
import { getHealth, getModelInfo } from './services/api';
import { speakText, getLocation } from './utils/helpers';
import en from './i18n/en.json';
import hi from './i18n/hi.json';
import ur from './i18n/ur.json';
import './styles/theme.css';

const translations = { en, hi, ur };

function App() {
  const [lang, setLang] = useState('en');
  const [modelReady, setModelReady] = useState(false);
  const [modelInfo, setModelInfo] = useState(null);
  const [confThreshold, setConfThreshold] = useState(0.25);
  const [imageSize, setImageSize] = useState(null);
  const [inferenceTime, setInferenceTime] = useState(null);
  const [location, setLocation] = useState(null);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [showHelp, setShowHelp] = useState(false);
  const prevDetectionsRef = useRef([]);
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
    getLocation().then(setLocation);
  }, []);

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

  useEffect(() => {
    if (!audioEnabled || !detections || detections.length === 0) return;
    const prev = prevDetectionsRef.current;
    const newDiseases = detections.filter(d =>
      !prev.some(p => p.class_name === d.class_name)
    );
    if (newDiseases.length > 0) {
      const diseaseNames = newDiseases.map(d => {
        const label = t.diseases[d.class_name] || d.class_name;
        return `${label} ${(d.confidence * 100).toFixed(0)}%`;
      }).join(', ');
      const greeting = t.app.title;
      speakText(`${greeting}. Detected: ${diseaseNames}`, lang);
    }
    prevDetectionsRef.current = detections;
  }, [detections, audioEnabled, lang, t]);

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

  const steps = [
    t.app.step1 || '📸 Take a photo of an apple leaf or fruit',
    t.app.step2 || '⬆️ Upload the image using the button above',
    t.app.step3 || '🤖 AI will analyze and detect diseases',
    t.app.step4 || '📋 Review results and get treatment advice'
  ];

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
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <LanguageSwitch lang={lang} onSwitch={setLang} t={t} />
        </div>
      </header>

      <div className="status-bar">
        <div className={`status-dot ${modelReady ? '' : 'loading'}`} />
        <span>{modelReady ? t.status.ready : t.status.loading}</span>
        {location && (
          <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--gray-500)' }}>
            📍 {location.lat}, {location.lng}
          </span>
        )}
        {processing && <span style={{ marginLeft: processing ? 0 : 'auto', fontSize: 14 }}>{t.status.processing}</span>}
      </div>

      <div className="help-bar">
        <button className="help-toggle" onClick={() => setShowHelp(!showHelp)}>
          {showHelp ? '✕' : '?'} {showHelp ? (t.app.closeHelp || 'Close') : (t.app.help || 'How to use')}
        </button>
      </div>

      {showHelp && (
        <div className="help-steps">
          <div className="help-title">{t.app.howToUse || 'How to use this app:'}</div>
          {steps.map((step, i) => (
            <div key={i} className="help-step">
              <span className="help-step-num">{i + 1}</span>
              <span>{step}</span>
            </div>
          ))}
          <div className="help-tip">
            💡 <strong>{t.app.tip || 'Tip:'}</strong> {t.app.helpTip || 'Point your camera at an apple tree leaf for best results. Use in daylight.'}
          </div>
        </div>
      )}

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
          audioEnabled={audioEnabled}
          onAudioToggle={() => setAudioEnabled(!audioEnabled)}
        />
      </div>

      <InstallPrompt />
    </div>
  );
}

export default App;
