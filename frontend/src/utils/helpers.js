export const drawDetections = (canvas, detections, options = {}) => {
  const { showLabels = true, lineWidth = 3, fontSize = 14 } = options;
  const ctx = canvas.getContext('2d');

  const boxColor = '#1a1a1a';
  const labelBg = 'rgba(26, 26, 26, 0.92)';
  const labelTextColor = '#ffffff';

  ctx.save();

  detections.forEach((det) => {
    const { xmin, ymin, xmax, ymax } = det.bbox;

    ctx.strokeStyle = boxColor;
    ctx.lineWidth = lineWidth;
    ctx.strokeRect(xmin, ymin, xmax - xmin, ymax - ymin);

    if (showLabels) {
      const label = `${det.class_name.replace(/_/g, ' ')} ${(det.confidence * 100).toFixed(1)}%`;
      ctx.font = `${fontSize}px -apple-system, BlinkMacSystemFont, sans-serif`;
      const metrics = ctx.measureText(label);
      const textWidth = metrics.width;
      const textHeight = fontSize + 8;

      ctx.fillStyle = labelBg;
      const labelY = Math.max(ymin, textHeight);
      ctx.fillRect(xmin, labelY - textHeight, textWidth + 8, textHeight);

      ctx.fillStyle = labelTextColor;
      ctx.fillText(label, xmin + 4, labelY - 4);
    }
  });

  ctx.restore();
};

export const getDiseaseColor = (className) => {
  return '#1a1a1a';
};

export const getDiseaseClass = (className) => {
  return className === 'healthy_apple' ? 'healthy' : 'disease';
};

export const formatConfidence = (confidence) => {
  return `${(confidence * 100).toFixed(1)}%`;
};

export const validateFile = (file, maxSizeMB = 16) => {
  if (!file) return 'No file selected';
  if (!file.type.startsWith('image/')) return 'Invalid file type. Please select an image.';
  if (file.size > maxSizeMB * 1024 * 1024) return `File too large. Maximum size is ${maxSizeMB}MB.`;
  return null;
};

export const compressImage = (file, maxWidth = 1920, quality = 0.7) => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      URL.revokeObjectURL(url);
      const canvas = document.createElement('canvas');
      let w = img.width;
      let h = img.height;
      if (w > maxWidth) {
        h = h * (maxWidth / w);
        w = maxWidth;
      }
      if (h > maxWidth) {
        w = w * (maxWidth / h);
        h = maxWidth;
      }
      canvas.width = Math.round(w);
      canvas.height = Math.round(h);
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        if (!blob) return reject(new Error('Image compression failed'));
        const compressedFile = new File([blob], file.name, { type: 'image/jpeg' });
        resolve(compressedFile);
      }, 'image/jpeg', quality);
    };
    img.onerror = reject;
    img.src = url;
  });
};

export const speakText = (text, lang = 'en') => {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang === 'ur' ? 'ur-PK' : lang === 'hi' ? 'hi-IN' : 'en-US';
  utterance.rate = 0.9;
  utterance.volume = 1;
  window.speechSynthesis.speak(utterance);
};

export const getLocation = () => {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude.toFixed(6), lng: pos.coords.longitude.toFixed(6) }),
      () => resolve(null),
      { timeout: 10000, enableHighAccuracy: false }
    );
  });
};

export const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
};
