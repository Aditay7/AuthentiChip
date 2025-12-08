# Scan API Documentation - Frontend Integration Guide

## Base URL
```
http://localhost:8000/api/v1
```

For production, replace with your actual backend URL.

---

## 📋 Table of Contents
1. [UI/UX Guide - What to Show](#uiux-guide---what-to-show-in-frontend)
2. [Capture Image](#1-capture-image)
3. [Process/Crop Image](#2-processcrop-image)
4. [Complete Workflow](#complete-workflow)
5. [Error Handling](#error-handling)
6. [Frontend Integration Examples](#frontend-integration-examples)

---

## UI/UX Guide - What to Show in Frontend

This section describes exactly what to display to users at each step of the scan workflow.

### 🎨 Recommended User Flow

```
[Initial] → [Capturing...] → [Captured ✓] → [Processing...] → [Complete ✓]
```

---

### **Step 1: Initial State (Before Capture)**

**What to show**:
- ✅ "Capture IC Image" button (primary action)
- ✅ Instructions: "Position the IC chip under the camera and click capture"
- ✅ User information (username, user_id) if applicable

**UI Example**:
```jsx
<div className="scan-container">
  <h2>IC Image Scan</h2>
  <p>Position the IC chip under the camera and click capture</p>
  
  <button className="btn-primary" onClick={handleCapture}>
    📸 Capture IC Image
  </button>
</div>
```

---

### **Step 2: Capturing State (During Capture API Call)**

**What to show**:
- ✅ Loading spinner/animation
- ✅ "Capturing image..." message
- ✅ Disable the capture button

**UI Example**:
```jsx
<div className="scan-container">
  <div className="loading-state">
    <div className="spinner"></div>
    <p>📸 Capturing image from camera...</p>
    <p className="subtext">Please wait...</p>
  </div>
  
  <button className="btn-primary" disabled>
    Capturing...
  </button>
</div>
```

**Duration**: 1-3 seconds

---

### **Step 3: Capture Success**

**What to show**:
- ✅ Success message: "Image captured successfully!"
- ✅ Scan ID (for reference)
- ✅ Original image preview (recommended)
- ✅ "Process Image" button (next action)

**Data Available**:
```json
{
  "scan_id": "675abc123def456789012345",
  "image_path": "original/capture_20251208_143903.jpg"
}
```

**UI Example**:
```jsx
<div className="scan-container">
  <div className="success-message">
    ✅ Image captured successfully!
  </div>
  
  <div className="scan-info">
    <p>Scan ID: <code>{scanId}</code></p>
  </div>
  
  {/* Optional: Show original image preview */}
  <div className="image-preview">
    <h3>Original Image</h3>
    <img 
      src={`http://localhost:8000/uploads/${imagePath}`}
      alt="Captured IC"
      style={{maxWidth: '400px', border: '2px solid #ddd'}}
    />
  </div>
  
  <button className="btn-primary" onClick={handleProcess}>
    🔄 Process & Crop Image
  </button>
</div>
```

---

### **Step 4: Processing State (During Process API Call)**

**What to show**:
- ✅ Loading spinner/animation
- ✅ "Processing image..." message
- ✅ Description: "Detecting IC, rotating, and cropping..."
- ✅ Disable the process button

**UI Example**:
```jsx
<div className="scan-container">
  <div className="loading-state">
    <div className="spinner"></div>
    <p>🔄 Processing image...</p>
    <p className="subtext">Detecting IC chip, rotating, and cropping...</p>
  </div>
  
  <button className="btn-primary" disabled>
    Processing...
  </button>
</div>
```

**Duration**: 2-5 seconds

---

### **Step 5: Complete Success (MOST IMPORTANT!)**

**What to show**:
- ✅ Success message: "Image processed successfully!"
- ✅ **Side-by-side comparison**: Original vs Cropped images
- ✅ Scan ID
- ✅ Action buttons: "New Scan", "Download", etc.

**Data Available**:
```json
{
  "scan_id": "675abc123def456789012345",
  "original_image_path": "original/capture_20251208_143903.jpg",
  "cropped_image_path": "cropped/cropped_20251208_143903.jpg"
}
```

**UI Example (Recommended)**:
```jsx
<div className="scan-container">
  <div className="success-banner">
    ✅ Image processed successfully!
  </div>
  
  <div className="scan-metadata">
    <p>Scan ID: <code>{scanId}</code></p>
    <p>Completed at: {new Date().toLocaleTimeString()}</p>
  </div>
  
  {/* Side-by-side image comparison - THIS IS KEY! */}
  <div className="image-comparison">
    <div className="image-column">
      <h3>Original Image</h3>
      <img 
        src={`http://localhost:8000/uploads/${originalImagePath}`}
        alt="Original IC"
        className="comparison-image"
      />
      <p className="image-label">Captured from camera</p>
    </div>
    
    <div className="arrow">→</div>
    
    <div className="image-column">
      <h3>Processed Image</h3>
      <img 
        src={`http://localhost:8000/uploads/${croppedImagePath}`}
        alt="Cropped IC"
        className="comparison-image highlight"
      />
      <p className="image-label">Detected, rotated & cropped</p>
    </div>
  </div>
  
  {/* Action buttons */}
  <div className="action-buttons">
    <button className="btn-primary" onClick={handleNewScan}>
      📸 New Scan
    </button>
    <button className="btn-secondary" onClick={handleDownload}>
      💾 Download Cropped Image
    </button>
  </div>
</div>
```

---

### **Error States**

#### **Capture Failed**
```jsx
<div className="scan-container">
  <div className="error-message">
    ❌ Capture failed: Cannot reach Raspberry Pi camera
  </div>
  
  <div className="error-details">
    <p>Please check:</p>
    <ul>
      <li>Camera is powered on</li>
      <li>Network connection is stable</li>
    </ul>
  </div>
  
  <button className="btn-primary" onClick={handleRetry}>
    🔄 Retry Capture
  </button>
</div>
```

#### **Processing Failed**
```jsx
<div className="scan-container">
  <div className="error-message">
    ❌ Processing failed: No IC chip detected in image
  </div>
  
  {/* Show the original image for reference */}
  <div className="image-preview">
    <h3>Captured Image</h3>
    <img src={`http://localhost:8000/uploads/${originalPath}`} alt="Failed" />
  </div>
  
  <button className="btn-primary" onClick={handleRecapture}>
    📸 Capture Again
  </button>
</div>
```

---

### **Visual Workflow Summary**

```
┌─────────────────────────────────────┐
│  Step 1: Initial                    │
│  [📸 Capture IC Image Button]       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Step 2: Capturing                  │
│  [Spinner] Capturing image...       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Step 3: Captured                   │
│  ✅ Image captured!                 │
│  [Preview of original image]        │
│  [🔄 Process & Crop Button]         │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Step 4: Processing                 │
│  [Spinner] Processing image...      │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Step 5: Complete ⭐                │
│  ✅ Image processed successfully!   │
│                                     │
│  ┌──────────┐    ┌──────────┐      │
│  │ Original │ →  │ Cropped  │      │
│  │ [Image]  │    │ [Image]  │      │
│  └──────────┘    └──────────┘      │
│                                     │
│  [📸 New Scan] [💾 Download]       │
└─────────────────────────────────────┘
```

---

### **Key Recommendations**

1. **Always show both images side-by-side** - This is the most important visual element
2. **Use loading states** - Users should know something is happening
3. **Provide clear error messages** - Help users understand what went wrong
4. **Include retry options** - Allow users to recover from errors
5. **Highlight the cropped image** - Make it clear which is the final result
6. **Add action buttons** - "New Scan", "Download", "View Details"

---

### **Recommended CSS**

```css
.image-comparison {
  display: flex;
  gap: 30px;
  align-items: center;
  justify-content: center;
  margin: 30px 0;
  flex-wrap: wrap;
}

.image-column {
  flex: 1;
  min-width: 300px;
  text-align: center;
}

.comparison-image {
  max-width: 100%;
  height: auto;
  border: 2px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.comparison-image.highlight {
  border-color: #28a745;
  box-shadow: 0 4px 12px rgba(40,167,69,0.3);
}

.arrow {
  font-size: 48px;
  color: #666;
}

.success-banner {
  background-color: #d4edda;
  color: #155724;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 18px;
  font-weight: bold;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
```

---

## 1. Capture Image

Captures an image from the Raspberry Pi camera and saves it to the database.

### Endpoint
```
POST /api/v1/scan/capture
```

### Query Parameters (Optional)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | string | No | MongoDB ObjectId of the user performing the scan |
| `username` | string | No | Username of the user performing the scan |

### Request Example

**JavaScript (Fetch API)**:
```javascript
const response = await fetch('http://localhost:8000/api/v1/scan/capture?user_id=675abc123&username=worker1', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  }
});

const data = await response.json();
console.log(data);
```

**Axios**:
```javascript
import axios from 'axios';

const response = await axios.post('http://localhost:8000/api/v1/scan/capture', null, {
  params: {
    user_id: '675abc123',
    username: 'worker1'
  }
});

console.log(response.data);
```

**cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/scan/capture?user_id=675abc123&username=worker1"
```

### Response

**Success (200 OK)**:
```json
{
  "scan_id": "675abc123def456789012345",
  "image_path": "original/capture_20251208_143335.jpg",
  "message": "Image captured and scan created successfully"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `scan_id` | string | MongoDB ObjectId of the created scan document. **Save this for the next step!** |
| `image_path` | string | Relative path to the saved original image |
| `message` | string | Success message |

### Error Responses

| Status Code | Description | Response Example |
|-------------|-------------|------------------|
| 502 | Pi capture failed | `{"detail": "Pi capture failed with status 500"}` |
| 503 | Cannot reach Raspberry Pi | `{"detail": "Cannot reach Raspberry Pi at http://172.17.18.197:5500/snapshot"}` |
| 504 | Pi timeout (>10 seconds) | `{"detail": "Raspberry Pi camera timeout - check if device is online"}` |
| 500 | Internal server error | `{"detail": "Failed to capture and save scan: ..."}` |

---

## 2. Process/Crop Image

Processes a captured image using SmartCropper (IC detection, rotation, and cropping).

### Endpoint
```
POST /api/v1/scan/{scan_id}/process
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | **Yes** | MongoDB ObjectId from the capture response |

### Request Example

**JavaScript (Fetch API)**:
```javascript
const scanId = '675abc123def456789012345'; // From capture response

const response = await fetch(`http://localhost:8000/api/v1/scan/${scanId}/process`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  }
});

const data = await response.json();
console.log(data);
```

**Axios**:
```javascript
import axios from 'axios';

const scanId = '675abc123def456789012345';

const response = await axios.post(`http://localhost:8000/api/v1/scan/${scanId}/process`);
console.log(response.data);
```

**cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/scan/675abc123def456789012345/process"
```

### Response

**Success (200 OK)**:
```json
{
  "scan_id": "675abc123def456789012345",
  "original_image_path": "original/capture_20251208_143335.jpg",
  "cropped_image_path": "cropped/cropped_20251208_143335.jpg",
  "message": "Image processed successfully"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `scan_id` | string | MongoDB ObjectId of the scan document |
| `original_image_path` | string | Relative path to the original captured image |
| `cropped_image_path` | string | Relative path to the processed/cropped image |
| `message` | string | Success message |

### Error Responses

| Status Code | Description | Response Example |
|-------------|-------------|------------------|
| 404 | Scan not found | `{"detail": "Scan with id 675abc123 not found"}` |
| 404 | Original image not found | `{"detail": "Original image not found at original/capture_...jpg"}` |
| 400 | No original image path | `{"detail": "Scan does not have an original image path"}` |
| 500 | Processing failed | `{"detail": "Image processing failed: No contours found"}` |
| 500 | Internal server error | `{"detail": "Failed to process scan image: ..."}` |

---

## Complete Workflow

### Step-by-Step Integration

```javascript
// Step 1: Capture image from Raspberry Pi camera
async function captureImage(userId, username) {
  try {
    const response = await fetch(`http://localhost:8000/api/v1/scan/capture?user_id=${userId}&username=${username}`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      throw new Error(`Capture failed: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('✅ Image captured:', data);
    return data.scan_id; // Return scan_id for next step
    
  } catch (error) {
    console.error('❌ Capture error:', error);
    throw error;
  }
}

// Step 2: Process/crop the captured image
async function processImage(scanId) {
  try {
    const response = await fetch(`http://localhost:8000/api/v1/scan/${scanId}/process`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      throw new Error(`Processing failed: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('✅ Image processed:', data);
    return data;
    
  } catch (error) {
    console.error('❌ Processing error:', error);
    throw error;
  }
}

// Complete workflow
async function captureAndProcessWorkflow(userId, username) {
  try {
    // Step 1: Capture
    const scanId = await captureImage(userId, username);
    
    // Step 2: Process
    const result = await processImage(scanId);
    
    console.log('🎉 Workflow complete!');
    console.log('Original image:', result.original_image_path);
    console.log('Cropped image:', result.cropped_image_path);
    
    return result;
    
  } catch (error) {
    console.error('❌ Workflow failed:', error);
    throw error;
  }
}

// Usage
captureAndProcessWorkflow('675abc123', 'worker1');
```

---

## Error Handling

### Recommended Error Handling Pattern

```javascript
async function captureImageWithErrorHandling(userId, username) {
  try {
    const response = await fetch(`http://localhost:8000/api/v1/scan/capture?user_id=${userId}&username=${username}`, {
      method: 'POST',
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      // Handle specific error codes
      switch (response.status) {
        case 503:
          alert('Cannot reach camera. Please check if Raspberry Pi is online.');
          break;
        case 504:
          alert('Camera timeout. Please try again.');
          break;
        case 502:
          alert('Camera capture failed. Please check camera hardware.');
          break;
        default:
          alert(`Error: ${data.detail || 'Unknown error'}`);
      }
      throw new Error(data.detail);
    }
    
    return data;
    
  } catch (error) {
    if (error.name === 'TypeError') {
      alert('Network error. Please check your connection.');
    }
    throw error;
  }
}
```

---

## Frontend Integration Examples

### React Example

```jsx
import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

function ScanComponent() {
  const [scanId, setScanId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleCapture = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/scan/capture`, null, {
        params: {
          user_id: 'user123',
          username: 'worker1'
        }
      });
      
      setScanId(response.data.scan_id);
      console.log('Captured:', response.data);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Capture failed');
    } finally {
      setLoading(false);
    }
  };

  const handleProcess = async () => {
    if (!scanId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/scan/${scanId}/process`);
      setResult(response.data);
      console.log('Processed:', response.data);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Processing failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCaptureAndProcess = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Step 1: Capture
      const captureResponse = await axios.post(`${API_BASE_URL}/scan/capture`, null, {
        params: { user_id: 'user123', username: 'worker1' }
      });
      
      const newScanId = captureResponse.data.scan_id;
      setScanId(newScanId);
      
      // Step 2: Process
      const processResponse = await axios.post(`${API_BASE_URL}/scan/${newScanId}/process`);
      setResult(processResponse.data);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Workflow failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>IC Scan Workflow</h2>
      
      <button onClick={handleCapture} disabled={loading}>
        {loading ? 'Capturing...' : 'Capture Image'}
      </button>
      
      <button onClick={handleProcess} disabled={!scanId || loading}>
        {loading ? 'Processing...' : 'Process Image'}
      </button>
      
      <button onClick={handleCaptureAndProcess} disabled={loading}>
        {loading ? 'Working...' : 'Capture & Process'}
      </button>
      
      {error && <div style={{color: 'red'}}>Error: {error}</div>}
      
      {scanId && <div>Scan ID: {scanId}</div>}
      
      {result && (
        <div>
          <h3>Result:</h3>
          <p>Original: {result.original_image_path}</p>
          <p>Cropped: {result.cropped_image_path}</p>
          <img 
            src={`http://localhost:8000/uploads/${result.cropped_image_path}`} 
            alt="Cropped IC"
            style={{maxWidth: '400px'}}
          />
        </div>
      )}
    </div>
  );
}

export default ScanComponent;
```

### Vue.js Example

```vue
<template>
  <div class="scan-component">
    <h2>IC Scan Workflow</h2>
    
    <button @click="captureAndProcess" :disabled="loading">
      {{ loading ? 'Processing...' : 'Capture & Process Image' }}
    </button>
    
    <div v-if="error" class="error">{{ error }}</div>
    
    <div v-if="result" class="result">
      <h3>Result:</h3>
      <p>Scan ID: {{ result.scan_id }}</p>
      <p>Original: {{ result.original_image_path }}</p>
      <p>Cropped: {{ result.cropped_image_path }}</p>
      <img 
        :src="`http://localhost:8000/uploads/${result.cropped_image_path}`" 
        alt="Cropped IC"
        style="max-width: 400px;"
      />
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'ScanComponent',
  data() {
    return {
      loading: false,
      result: null,
      error: null,
      apiBaseUrl: 'http://localhost:8000/api/v1'
    };
  },
  methods: {
    async captureAndProcess() {
      this.loading = true;
      this.error = null;
      this.result = null;
      
      try {
        // Step 1: Capture
        const captureResponse = await axios.post(`${this.apiBaseUrl}/scan/capture`, null, {
          params: {
            user_id: this.$store.state.userId,
            username: this.$store.state.username
          }
        });
        
        const scanId = captureResponse.data.scan_id;
        
        // Step 2: Process
        const processResponse = await axios.post(`${this.apiBaseUrl}/scan/${scanId}/process`);
        this.result = processResponse.data;
        
      } catch (err) {
        this.error = err.response?.data?.detail || 'Operation failed';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.error {
  color: red;
  margin: 10px 0;
}
.result {
  margin-top: 20px;
}
</style>
```

### TypeScript Interfaces

```typescript
// API Response Types
interface CaptureResponse {
  scan_id: string;
  image_path: string;
  message: string;
}

interface ProcessResponse {
  scan_id: string;
  original_image_path: string;
  cropped_image_path: string;
  message: string;
}

interface ErrorResponse {
  detail: string;
}

// API Service
class ScanAPI {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000/api/v1') {
    this.baseUrl = baseUrl;
  }

  async capture(userId?: string, username?: string): Promise<CaptureResponse> {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    if (username) params.append('username', username);

    const response = await fetch(`${this.baseUrl}/scan/capture?${params}`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error: ErrorResponse = await response.json();
      throw new Error(error.detail);
    }

    return response.json();
  }

  async process(scanId: string): Promise<ProcessResponse> {
    const response = await fetch(`${this.baseUrl}/scan/${scanId}/process`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error: ErrorResponse = await response.json();
      throw new Error(error.detail);
    }

    return response.json();
  }

  async captureAndProcess(userId?: string, username?: string): Promise<ProcessResponse> {
    const captureResult = await this.capture(userId, username);
    return this.process(captureResult.scan_id);
  }
}

// Usage
const scanAPI = new ScanAPI();

async function runWorkflow() {
  try {
    const result = await scanAPI.captureAndProcess('user123', 'worker1');
    console.log('Success:', result);
  } catch (error) {
    console.error('Error:', error);
  }
}
```

---

## Image Display

To display the captured or cropped images in your frontend:

```javascript
// Construct full image URL
const imageUrl = `http://localhost:8000/uploads/${imagePath}`;

// Example:
// http://localhost:8000/uploads/original/capture_20251208_143335.jpg
// http://localhost:8000/uploads/cropped/cropped_20251208_143335.jpg
```

**HTML**:
```html
<img src="http://localhost:8000/uploads/cropped/cropped_20251208_143335.jpg" alt="Cropped IC" />
```

**React**:
```jsx
<img src={`http://localhost:8000/uploads/${result.cropped_image_path}`} alt="Cropped IC" />
```

---

## Configuration

### Camera Endpoint

The Raspberry Pi camera endpoint is configured in the backend:
- **Current**: `http://172.17.18.197:5500/snapshot`
- **Configurable via**: `.env` file using `PI_CAPTURE_URL` variable

If you need to change it, update the backend `.env` file and restart the server.

---

## Notes

1. **CORS**: The backend has CORS enabled for all origins (`*`). For production, configure specific allowed origins.

2. **Timeouts**: Camera capture has a 10-second timeout. If the Pi doesn't respond within this time, you'll get a 504 error.

3. **Image Paths**: All image paths returned are relative to the `uploads/` directory on the backend server.

4. **Scan ID**: Always save the `scan_id` from the capture response - you'll need it for processing and future operations.

5. **Processing**: The SmartCropper automatically detects the IC body, rotates it to the correct orientation, and crops to the IC boundaries.

---

## Support

For issues or questions:
- Check backend logs: `uvicorn app.main:app --reload`
- Verify Raspberry Pi is accessible: `curl http://172.17.18.197:5500/snapshot`
- Check MongoDB connection
- Verify `uploads/` directory permissions
