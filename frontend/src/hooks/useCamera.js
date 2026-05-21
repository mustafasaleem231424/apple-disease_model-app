import { useState, useRef, useCallback, useEffect } from 'react';

export function useCamera(options = {}) {
  const { facingMode = 'environment', width = 640, height = 480 } = options;
  const [active, setActive] = useState(false);
  const [error, setError] = useState(null);
  const [permission, setPermission] = useState('prompt');
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const start = useCallback(async () => {
    try {
      setError(null);
      
      if (navigator.permissions) {
        try {
          const result = await navigator.permissions.query({ name: 'camera' });
          setPermission(result.state);
          result.addEventListener('change', () => setPermission(result.state));
        } catch (e) {
          console.warn('Permission API not supported');
        }
      }

      const constraints = {
        video: {
          facingMode: { ideal: facingMode },
          width: { ideal: width },
          height: { ideal: height }
        },
        audio: false
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      
      streamRef.current = stream;
      setActive(true);
    } catch (err) {
      if (err.name === 'NotAllowedError') {
        setError('Camera access denied. Please enable camera permissions in your browser settings.');
      } else if (err.name === 'NotFoundError') {
        setError('No camera found on this device.');
      } else {
        setError(`Camera error: ${err.message}`);
      }
      console.error('Camera error:', err);
    }
  }, [facingMode, width, height]);

  const stop = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setActive(false);
  }, []);

  const captureFrame = useCallback(() => {
    if (!videoRef.current || !active) return null;
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    return canvas;
  }, [active]);

  const captureBlob = useCallback((quality = 0.85) => {
    const canvas = captureFrame();
    if (!canvas) return null;
    return new Promise((resolve) => {
      canvas.toBlob((blob) => resolve(blob), 'image/jpeg', quality);
    });
  }, [captureFrame]);

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  return {
    videoRef,
    active,
    error,
    permission,
    start,
    stop,
    captureFrame,
    captureBlob
  };
}
