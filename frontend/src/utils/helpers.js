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
    let xmin, ymin, xmax, ymax;
    if (Array.isArray(det.bbox)) {
      [xmin, ymin, xmax, ymax] = det.bbox;
    } else if (det.bbox) {
      xmin = det.bbox.xmin;
      ymin = det.bbox.ymin;
      xmax = det.bbox.xmax;
      ymax = det.bbox.ymax;
    } else {
      return;
    }

    const color = getDiseaseColor(det.class_name);
    const width = xmax - xmin;
    const height = ymax - ymin;
    
    // 1. Draw precision main rectangle
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.strokeRect(xmin, ymin, width, height);

    // 2. Draw high-precision corner brackets for focused target lock
    const cornerLength = Math.min(20, Math.min(width, height) * 0.25);
    ctx.lineWidth = lineWidth + 1.5;
    
    // Top-Left corner
    ctx.beginPath();
    ctx.moveTo(xmin, ymin + cornerLength);
    ctx.lineTo(xmin, ymin);
    ctx.lineTo(xmin + cornerLength, ymin);
    ctx.stroke();
    
    // Top-Right corner
    ctx.beginPath();
    ctx.moveTo(xmax - cornerLength, ymin);
    ctx.lineTo(xmax, ymin);
    ctx.lineTo(xmax, ymin + cornerLength);
    ctx.stroke();

    // Bottom-Left corner
    ctx.beginPath();
    ctx.moveTo(xmin, ymax - cornerLength);
    ctx.lineTo(xmin, ymax);
    ctx.lineTo(xmin + cornerLength, ymax);
    ctx.stroke();

    // Bottom-Right corner
    ctx.beginPath();
    ctx.moveTo(xmax - cornerLength, ymax);
    ctx.lineTo(xmax, ymax);
    ctx.lineTo(xmax, ymax - cornerLength);
    ctx.stroke();

    // 3. Draw high-visibility label tag
    if (showLabels) {
      const labelText = `${det.class_name.replace(/_/g, ' ').toUpperCase()} ${(det.confidence * 100).toFixed(0)}%`;
      ctx.font = `bold ${fontSize}px 'Outfit', -apple-system, sans-serif`;
      const metrics = ctx.measureText(labelText);
      const textWidth = metrics.width;
      const textHeight = fontSize + 8;
      
      const labelY = Math.max(ymin, textHeight + 2);
      
      // Label background pill
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.roundRect ? ctx.roundRect(xmin, labelY - textHeight, textWidth + 12, textHeight, [4, 4, 0, 0]) : ctx.fillRect(xmin, labelY - textHeight, textWidth + 12, textHeight);
      ctx.fill();
      
      // Label text
      const lightBackgrounds = ['apple_scab', 'powdery_mildew', 'healthy_apple'];
      ctx.fillStyle = lightBackgrounds.includes(det.class_name) ? '#050806' : '#ffffff';
      ctx.fillText(labelText, xmin + 6, labelY - 6);
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
