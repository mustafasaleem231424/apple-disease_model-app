import { useState, useRef, useCallback, useEffect } from 'react';

export function useCamera(options = {}) {
  const { facingMode = 'environment', width = 640, height = 480 } = options;
  const [active, setActive] = useState(false);
  const [error, setError] = useState(null);
  const [permission, setPermission] = useState('prompt');
  const [devices, setDevices] = useState([]);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  // Get list of available camera sources
  const refreshDevices = useCallback(async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
        return;
      }
      const allDevices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = allDevices.filter(d => d.kind === 'videoinput');
      setDevices(videoDevices);
    } catch (e) {
      console.warn('Could not enumerate media devices:', e);
    }
  }, []);

  const start = useCallback(async (selectedDeviceId = null) => {
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

      // Base video constraints
      const videoConstraints = selectedDeviceId 
        ? { deviceId: { exact: selectedDeviceId } }
        : { facingMode: { ideal: facingMode } };

      videoConstraints.width = { ideal: width };
      videoConstraints.height = { ideal: height };

      const constraints = {
        video: videoConstraints,
        audio: false
      };

      // Stop any existing tracks
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      
      streamRef.current = stream;
      setActive(true);
      
      // Update device list after getting permission
      await refreshDevices();
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
  }, [facingMode, width, height, refreshDevices]);

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
    
    // Ensure video has loaded properties
    if (video.videoWidth === 0 || video.videoHeight === 0) return null;

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
    // Initial check for camera sources
    refreshDevices();
    
    // Listen for device changes (plugs/unplugs)
    if (navigator.mediaDevices && navigator.mediaDevices.addEventListener) {
      navigator.mediaDevices.addEventListener('devicechange', refreshDevices);
    }
    
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (navigator.mediaDevices && navigator.mediaDevices.removeEventListener) {
        navigator.mediaDevices.removeEventListener('devicechange', refreshDevices);
      }
    };
  }, [refreshDevices]);

  return {
    videoRef,
    active,
    error,
    permission,
    devices,
    start,
    stop,
    captureFrame,
    captureBlob,
    refreshDevices
  };
}
