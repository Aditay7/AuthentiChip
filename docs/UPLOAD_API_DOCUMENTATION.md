# Image Upload API - Implementation Summary

## ✅ What Was Built

I've successfully implemented the **`POST /api/v1/scan/upload`** endpoint that allows users to upload images directly from the frontend.

---

## 📁 Files Created & Modified

### Modified Files

#### 1. [camera_service.py](file:///Users/aditay/Documents/Authentichip/backend/app/services/camera_service.py#L104-L142)
- **Added**: `save_uploaded_file()` method
- Handles file uploads from frontend
- Validates and saves files with timestamp-based naming
- Stores files in `uploads/original/` directory

#### 2. [scan.py](file:///Users/aditay/Documents/Authentichip/backend/app/api/v1/scan.py#L122-L247)
- **Added**: `POST /upload` endpoint
- Accepts multipart/form-data file uploads
- Validates file type (JPG, JPEG, PNG only)
- Validates file size (max 10MB)
- Creates scan document in MongoDB

---

## 🚀 API Endpoint

### **POST /api/v1/scan/upload**

Upload an image file and create a scan record.

**Content-Type**: `multipart/form-data`

**Form Data**:
- `file` (required) - Image file (JPG, JPEG, PNG)

**Query Parameters** (Optional):
- `user_id` - MongoDB ObjectId of the user
- `username` - Username of the user

**Example Request (JavaScript)**:
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/api/v1/scan/upload?user_id=user123&username=worker1', {
  method: 'POST',
  body: formData
});

const data = await response.json();
console.log(data);
```

**Example Request (curl)**:
```bash
curl -X POST "http://localhost:8000/api/v1/scan/upload?user_id=user123&username=worker1" \
  -F "file=@/path/to/image.jpg"
```

**Success Response (200 OK)**:
```json
{
  "scan_id": "675abc123def456789012345",
  "image_path": "original/upload_20251208_152604.jpg",
  "message": "Image uploaded and scan created successfully"
}
```

**Error Responses**:

| Status Code | Description | Response Example |
|-------------|-------------|------------------|
| 400 | No file provided | `{"detail": "No file uploaded"}` |
| 400 | Invalid file type | `{"detail": "Invalid file type. Only JPG, JPEG, PNG allowed"}` |
| 413 | File too large | `{"detail": "File size exceeds 10MB limit"}` |
| 500 | Server error | `{"detail": "Failed to save uploaded image: ..."}` |

---

## 🔍 How It Works

1. **Frontend uploads file** via multipart/form-data
2. **Backend validates**:
   - File is provided
   - File type is JPG, JPEG, or PNG
   - File size is under 10MB
3. **Save to disk**: `uploads/original/upload_YYYYMMDD_HHMMSS.{ext}`
4. **Create scan document** in MongoDB with:
   - `original_image_path`: Path to uploaded file
   - `cropped_image_path`: null (to be filled by process endpoint)
   - User tracking info (if provided)
   - Timestamps
5. **Return scan_id** for use with process endpoint

---

## 📊 Complete Workflow

### Option 1: Upload → Process

```javascript
// Step 1: Upload image
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch('http://localhost:8000/api/v1/scan/upload', {
  method: 'POST',
  body: formData
});

const uploadData = await uploadResponse.json();
const scanId = uploadData.scan_id;

// Step 2: Process the uploaded image
const processResponse = await fetch(`http://localhost:8000/api/v1/scan/${scanId}/process`, {
  method: 'POST'
});

const processData = await processResponse.json();
console.log('Original:', processData.original_image_path);
console.log('Cropped:', processData.cropped_image_path);
```

### Option 2: Capture → Process (Existing)

```javascript
// Step 1: Capture from Pi camera
const captureResponse = await fetch('http://localhost:8000/api/v1/scan/capture', {
  method: 'POST'
});

const captureData = await captureResponse.json();
const scanId = captureData.scan_id;

// Step 2: Process the captured image
const processResponse = await fetch(`http://localhost:8000/api/v1/scan/${scanId}/process`, {
  method: 'POST'
});
```

---

## 🧪 Testing

### Test with curl

```bash
# Upload an image
curl -X POST "http://localhost:8000/api/v1/scan/upload" \
  -F "file=@test_image.jpg"

# Upload with user info
curl -X POST "http://localhost:8000/api/v1/scan/upload?user_id=user123&username=worker1" \
  -F "file=@test_image.jpg"
```

### Test with Postman

1. **Method**: POST
2. **URL**: `http://localhost:8000/api/v1/scan/upload`
3. **Body**: 
   - Select "form-data"
   - Key: `file` (change type to "File")
   - Value: Select your image file
4. **Query Params** (optional):
   - `user_id`: `user123`
   - `username`: `worker1`
5. **Send**

### Test with HTML Form

```html
<!DOCTYPE html>
<html>
<body>
  <h2>Upload IC Image</h2>
  <form id="uploadForm">
    <input type="file" id="fileInput" accept="image/jpeg,image/jpg,image/png" required>
    <button type="submit">Upload</button>
  </form>
  
  <div id="result"></div>
  
  <script>
    document.getElementById('uploadForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const formData = new FormData();
      formData.append('file', document.getElementById('fileInput').files[0]);
      
      try {
        const response = await fetch('http://localhost:8000/api/v1/scan/upload', {
          method: 'POST',
          body: formData
        });
        
        const data = await response.json();
        document.getElementById('result').innerHTML = `
          <p>Success! Scan ID: ${data.scan_id}</p>
          <p>Image Path: ${data.image_path}</p>
        `;
      } catch (error) {
        document.getElementById('result').innerHTML = `<p>Error: ${error.message}</p>`;
      }
    });
  </script>
</body>
</html>
```

---

## 📋 All Available Endpoints

Now you have **3 endpoints** for image handling:

| Endpoint | Method | Purpose | Input |
|----------|--------|---------|-------|
| `/api/v1/scan/capture` | POST | Capture from Pi camera | Query params (optional) |
| `/api/v1/scan/upload` | POST | Upload image file | File + Query params |
| `/api/v1/scan/{scan_id}/process` | POST | Process/crop image | scan_id |

---

## 🎯 Use Cases

### Use Case 1: Pi Camera Workflow
```
User → Click "Capture" → Pi Camera → Save → Process → Show Results
```

### Use Case 2: File Upload Workflow
```
User → Select File → Upload → Save → Process → Show Results
```

Both workflows converge at the **process** step!

---

## ✅ Validation Rules

**File Type**:
- ✅ Allowed: JPG, JPEG, PNG
- ❌ Rejected: GIF, BMP, TIFF, WebP, etc.

**File Size**:
- ✅ Allowed: Up to 10MB
- ❌ Rejected: Larger than 10MB

**File Naming**:
- Pattern: `upload_YYYYMMDD_HHMMSS.{ext}`
- Example: `upload_20251208_152604.jpg`
- Stored in: `uploads/original/`

---

## 🔧 Configuration

The file size limit is currently hardcoded to 10MB. To change it, modify:

**File**: `app/api/v1/scan.py` (line ~179)
```python
max_size = 10 * 1024 * 1024  # Change this value
```

Or add to `config.py`:
```python
MAX_UPLOAD_SIZE_MB: int = Field(default=10, ...)
```

---

## 📝 Summary

**What was built**:
- ✅ File upload endpoint (`POST /scan/upload`)
- ✅ File type validation (JPG, JPEG, PNG)
- ✅ File size validation (10MB limit)
- ✅ Save to disk with timestamp naming
- ✅ Create scan document in MongoDB
- ✅ Return scan_id for processing

**Where files are located**:
- **Service**: `app/services/camera_service.py` (save_uploaded_file method)
- **API**: `app/api/v1/scan.py` (upload endpoint)
- **Storage**: `uploads/original/upload_*.{ext}`

**How to use**:
1. Upload image via `/scan/upload`
2. Get `scan_id` from response
3. Process image via `/scan/{scan_id}/process`
4. Get both original and cropped image paths

The upload API is now ready for frontend integration! 🚀
