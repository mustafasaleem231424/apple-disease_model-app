const DISEASE_COLORS = {
  apple_scab: '#f59e0b',        // Amber / Yellow-orange
  black_rot: '#ef4444',         // Red / High severity
  cedar_apple_rust: '#f97316',  // Bright Orange
  powdery_mildew: '#06b6d4',    // Cyan / Light Blue
  healthy_apple: '#10b981',     // Emerald Green
  other: '#6b7280'              // Gray
};

export const getDiseaseColor = (className) => {
  return DISEASE_COLORS[className] || '#10b981';
};

export const drawDetections = (canvas, detections, options = {}) => {
  const { showLabels = true, lineWidth = 3, fontSize = 13 } = options;
  const ctx = canvas.getContext('2d');
  
  ctx.save();
  
  detections.forEach((det) => {
    const { xmin, ymin, xmax, ymax } = det.bbox;
    const color = getDiseaseColor(det.class_name);
    
    // Draw bounding box around the exact disease coordinates
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.strokeRect(xmin, ymin, xmax - xmin, ymax - ymin);

    if (showLabels) {
      const labelText = `${det.class_name.replace(/_/g, ' ').toUpperCase()} ${(det.confidence * 100).toFixed(0)}%`;
      ctx.font = `bold ${fontSize}px 'Outfit', -apple-system, sans-serif`;
      const metrics = ctx.measureText(labelText);
      const textWidth = metrics.width;
      const textHeight = fontSize + 8;
      
      // Draw background pill tag for exact label details
      ctx.fillStyle = color;
      const labelY = Math.max(ymin, textHeight);
      ctx.fillRect(xmin, labelY - textHeight, textWidth + 10, textHeight);
      
      // Draw contrast text (dark text for bright backgrounds)
      const lightBackgrounds = ['apple_scab', 'powdery_mildew', 'healthy_apple'];
      ctx.fillStyle = lightBackgrounds.includes(det.class_name) ? '#050806' : '#ffffff';
      ctx.fillText(labelText, xmin + 5, labelY - 6);
    }
  });
  
  ctx.restore();
};

export const getDiseaseClass = (className) => {
  return className === 'healthy_apple' ? 'healthy' : 'disease';
};

export const formatConfidence = (confidence) => {
  return `${(confidence * 100).toFixed(0)}%`;
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
