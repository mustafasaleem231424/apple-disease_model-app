import { useState, useCallback } from 'react';
import * as api from '../services/api';

export function useDetection() {
  const [detections, setDetections] = useState([]);
  const [annotatedImage, setAnnotatedImage] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);

  const detectImage = useCallback(async (file, confThreshold = 0.25) => {
    setProcessing(true);
    setError(null);
    try {
      const result = await api.detectImage(file, confThreshold);
      setDetections(result.detections || []);
      setAnnotatedImage(result.annotated_image || null);
      return result;
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Detection failed';
      setError(msg);
      throw err;
    } finally {
      setProcessing(false);
    }
  }, []);

  const processFrame = useCallback(async (file, confThreshold = 0.25) => {
    try {
      const result = await api.processFrame(file, confThreshold);
      setDetections(result.detections || []);
      setAnnotatedImage(result.annotated_frame || null);
      return result;
    } catch (err) {
      console.error('Frame processing failed:', err);
      return null;
    }
  }, []);

  const loadHistory = useCallback(async () => {
    try {
      const data = await api.getHistory();
      setHistory(data.history || []);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  }, []);

  const clearHistory = useCallback(async () => {
    try {
      await api.clearHistory();
      setHistory([]);
      setDetections([]);
      setAnnotatedImage(null);
    } catch (err) {
      console.error('Failed to clear history:', err);
    }
  }, []);

  const reset = useCallback(() => {
    setDetections([]);
    setAnnotatedImage(null);
    setError(null);
    setProcessing(false);
  }, []);

  return {
    detections,
    annotatedImage,
    processing,
    error,
    history,
    detectImage,
    processFrame,
    loadHistory,
    clearHistory,
    reset
  };
}
