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

export const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
};
