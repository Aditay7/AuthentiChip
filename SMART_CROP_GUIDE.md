# Smart Crop Testing Guide

Your `smart_crop.py` has **two modes**: Pi Mode and Folder Mode.

## Mode 1: Pi Mode (Fetch from Raspberry Pi Camera)

Fetches an image from your Raspberry Pi camera endpoint and crops it.

### Usage:

```bash
cd /Users/aditay/Documents/Authentichip/backend

# Fetch from your Raspberry Pi camera
python app/services/crop_dimensions/smart_crop.py pi \
  --url http://192.168.12.106:5500/snapshot \
  --output pi-crop-imgs
```

### What it does:
1. Fetches image from the URL
2. Crops the IC (removes pins)
3. Saves **only the cropped image** to `pi-crop-imgs/pi_capture_TIMESTAMP.jpg`
4. Prints dimensions and angle

### Output:
```
--- Pi Mode: Fetching from http://192.168.12.106:5500/snapshot ---
GET http://192.168.12.106:5500/snapshot...

SUCCESS: Image saved to pi-crop-imgs/pi_capture_20231206_183551.jpg
Dimensions: 1024.50 x 512.30 pixels
Angle Corrected: 2.50 degrees
```

---

## Mode 2: Folder Mode (Batch Process Local Images)

Processes all images in a folder and creates a cropped version of each.

### Usage:

```bash
# Process all images in a folder
python app/services/crop_dimensions/smart_crop.py folder \
  --input /path/to/your/ic_images
```

### What it does:
1. Finds all images in the input folder (recursively)
2. Crops each IC image
3. Creates a new folder: `ic_images-cropped/`
4. Saves cropped images maintaining folder structure
5. Creates `ic_dimensions.txt` with all measurements

### Example:

```bash
# If you have images in a folder called "test_images"
python app/services/crop_dimensions/smart_crop.py folder \
  --input test_images
```

### Output Structure:
```
test_images/               # Original folder
test_images-cropped/       # New folder created
  ├── ic_dimensions.txt    # CSV with all dimensions
  ├── image1.jpg          # Cropped version
  ├── image2.jpg          # Cropped version
  └── subfolder/
      └── image3.jpg      # Maintains folder structure
```

### Output File (`ic_dimensions.txt`):
```
Filename, Width, Height, Angle
image1.jpg, 1024.50, 512.30, 2.50
image2.jpg, 980.20, 490.10, -1.20
subfolder/image3.jpg, 1100.00, 550.00, 0.50
```

---

## Quick Tests

### Test 1: Single Image from Camera

```bash
# Make sure your Raspberry Pi camera is accessible first
ping 192.168.12.106

# Then run
python app/services/crop_dimensions/smart_crop.py pi \
  --url http://192.168.12.106:5500/snapshot
```

### Test 2: Batch Process Local Images

```bash
# Create a test folder with some IC images
mkdir test_ic_images
# Copy some IC images into it

# Process them
python app/services/crop_dimensions/smart_crop.py folder \
  --input test_ic_images

# Check results
ls -la test_ic_images-cropped/
cat test_ic_images-cropped/ic_dimensions.txt
```

---

## Important Notes

### Pi Mode:
- ❌ Does NOT save original image
- ✅ Saves only cropped image
- ❌ Does NOT save to database
- ✅ Uses timestamp for filename
- ✅ Good for quick testing

### Folder Mode:
- ❌ Does NOT save original images
- ✅ Saves only cropped images
- ❌ Does NOT save to database
- ✅ Creates CSV with dimensions
- ✅ Good for batch processing

### Network Issues:
If Pi mode fails with "No route to host":
1. Check if Raspberry Pi is on same network
2. Try: `ping 192.168.12.106`
3. Try: `curl http://192.168.12.106:5500/snapshot -o test.jpg`
4. Make sure both devices are on same WiFi

---

## Example Workflow

### Scenario: Test cropping on multiple images

```bash
# 1. Create test folder
mkdir my_ic_images

# 2. Add some IC images to the folder
# (copy your test images here)

# 3. Run smart_crop
python app/services/crop_dimensions/smart_crop.py folder --input my_ic_images

# 4. Check results
ls -la my_ic_images-cropped/

# 5. View dimensions
cat my_ic_images-cropped/ic_dimensions.txt

# 6. Open cropped images
open my_ic_images-cropped/*.jpg
```

---

## Comparison with Deleted Endpoints

| Feature | smart_crop.py | Deleted API Endpoints |
|---------|--------------|----------------------|
| **Type** | Command-line tool | REST API |
| **Original Image** | Not saved | Saved to disk |
| **Cropped Image** | Saved to disk | Saved to disk |
| **Database** | No | Yes (MongoDB) |
| **ObjectId** | No (uses timestamp) | Yes |
| **Use Case** | Testing, batch processing | Production, frontend integration |

---

## Help Command

```bash
# See all options
python app/services/crop_dimensions/smart_crop.py --help

# See pi mode options
python app/services/crop_dimensions/smart_crop.py pi --help

# See folder mode options
python app/services/crop_dimensions/smart_crop.py folder --help
```
