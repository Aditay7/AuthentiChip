# IC Datasheet Extractor Integration

This integration provides automated IC datasheet extraction and dimension analysis using Gemini AI.

## 🚀 Features

- **Automated Scraping**: Automatically finds and downloads IC datasheets from alldatasheet.com
- **AI-Powered Extraction**: Uses Google's Gemini AI to extract precise dimensional data
- **Multiple Input Methods**: 
  - Scrape by IC part number
  - Upload PDF file directly
  - Provide PDF URL
- **Production-Ready**: Async execution, proper error handling, and comprehensive logging

## 📋 Prerequisites

- Python 3.9+
- Google Chrome (for Selenium)
- Gemini API key from Google AI Studio

## 🛠️ Setup Instructions

### 1. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

All required packages are already in `requirements.txt`:
- `selenium` - Web scraping
- `webdriver-manager` - Automatic ChromeDriver management
- `google-generativeai` - Gemini AI integration
- `fastapi` - API framework
- `python-multipart` - File upload support
- `requests` - HTTP client
- `pytest` - Testing framework

### 3. Set Environment Variables

Create or update your `.env` file:

```bash
# Add to .env file
GEMINI_API_KEY=your_gemini_api_key_here
```

**Get your Gemini API key:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy and paste it into your `.env` file

### 4. Verify Setup

Check that the API key is loaded:

```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key:', 'SET' if os.getenv('GEMINI_API_KEY') else 'NOT SET')"
```

## 🏃 Running the Server

### Start the Development Server

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The server will start at: **http://localhost:8000**

### Verify Server is Running

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "ok"}
```

## 📡 API Endpoints

### 1. Scrape and Extract IC Datasheet

**Endpoint:** `GET /api/v1/extract/scrape/{ic_name}`

Automatically finds, downloads, and extracts dimensions from IC datasheet.

**Parameters:**
- `ic_name` (path): IC part number (e.g., HT12D, SN74HCT257N)
- `save_pdf` (query, optional): Save PDF to disk (default: true)

**Example:**
```bash
curl http://localhost:8000/api/v1/extract/scrape/HT12D | jq
```

**Response:**
```json
{
  "chip": "HT12D",
  "pdf_url": "https://...",
  "dimensions": {
    "manufacturer": "Holtek",
    "base_part_number": "HT12D",
    "package_type": "DIP-18",
    "body_length_nom_mm": 22.86,
    "body_width_nom_mm": 6.35,
    ...
  }
}
```

### 2. Extract from Uploaded PDF File

**Endpoint:** `POST /api/v1/extract/from-file`

Upload a PDF datasheet and extract dimensions.

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/extract/from-file \
  -F "pdf=@/path/to/datasheet.pdf" | jq
```

**Response:**
```json
{
  "file": "datasheet.pdf",
  "dimensions": { ... }
}
```

### 3. Extract from PDF URL

**Endpoint:** `POST /api/v1/extract/from-url`

Provide a direct URL to a PDF datasheet.

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/extract/from-url \
  -F "pdf_url=https://www.ti.com/lit/ds/symlink/sn74hct257.pdf" | jq
```

**Response:**
```json
{
  "pdf_url": "https://...",
  "dimensions": { ... }
}
```

### 4. Health Check

**Endpoint:** `GET /api/v1/extract/health`

Check if the extraction service is running.

**Example:**
```bash
curl http://localhost:8000/api/v1/extract/health | jq
```

## 🧪 Running Tests

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test File

```bash
# Unit tests
pytest tests/test_extractor_service.py -v

# Integration tests
pytest tests/test_api_extract.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=app.services.web_scapper --cov=app.api.v1.extract -v
```

## 📮 Using Postman

### Import Collection

1. Open Postman
2. Click **Import**
3. Select `postman/IC-Extractor-collection.json`
4. The collection will be imported with all endpoints

### Set Environment

1. Create a new environment in Postman
2. Add variable: `baseUrl` = `http://localhost:8000`
3. Select this environment before making requests

### Test Endpoints

The collection includes:
- ✅ Scrape and Extract IC Datasheet
- ✅ Extract from Uploaded PDF File
- ✅ Extract from PDF URL
- ✅ Health Check
- ✅ Example requests for common ICs (HT12D, SN74HCT257N, LM358)

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── extract.py          # API router with endpoints
│   ├── services/
│   │   └── web_scapper/
│   │       ├── gemini_extractor.py # Core extraction service
│   │       └── web_scrapping.py    # Original scraping code
│   └── main.py                     # FastAPI app with router registration
├── tests/
│   ├── test_extractor_service.py   # Unit tests
│   └── test_api_extract.py         # Integration tests
├── postman/
│   └── IC-Extractor-collection.json # Postman collection
├── downloads/                       # Downloaded PDFs (auto-created)
├── requirements.txt
└── .env                            # Environment variables
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |

### Downloads Directory

PDFs are saved to `downloads/{ic_name}.pdf` by default. This directory is created automatically.

To disable saving PDFs:
```bash
curl "http://localhost:8000/api/v1/extract/scrape/HT12D?save_pdf=false"
```

## 🐛 Troubleshooting

### "GEMINI_API_KEY environment variable is required"

**Solution:** Make sure your `.env` file contains the API key and is in the project root.

### ChromeDriver Issues

**Solution:** The `webdriver-manager` package automatically downloads and manages ChromeDriver. Ensure Chrome is installed on your system.

### "No datasheet found"

**Solution:** The IC part number might not exist on alldatasheet.com. Try:
- Verifying the part number spelling
- Using the full part number with package suffix (e.g., SN74HCT257N)
- Checking alldatasheet.com manually

### Timeout Errors

**Solution:** The scraping process can take 10-30 seconds. If you're getting timeouts:
- Check your internet connection
- Verify alldatasheet.com is accessible
- Increase timeout in `download_pdf()` function

## 📊 Example Output

```json
{
  "chip": "SN74HCT257N",
  "pdf_url": "https://www.alldatasheet.com/datasheet-pdf/pdf/...",
  "dimensions": {
    "manufacturer": "Texas Instruments",
    "base_part_number": "SN74HCT257",
    "full_part_numbers": ["SN74HCT257N", "SN74HCT257NE4"],
    "allowed_markings": ["SN74HCT257N"],
    "package_type": "PDIP-16",
    "body_length_min_mm": 18.92,
    "body_length_nom_mm": 19.305,
    "body_length_max_mm": 19.69,
    "body_width_min_mm": 6.1,
    "body_width_nom_mm": 6.35,
    "body_width_max_mm": 6.6,
    "pin_pitch_nom_mm": 2.54,
    "pin_width_min_mm": 0.38,
    "pin_width_nom_mm": 0.455,
    "pin_width_max_mm": 0.53,
    ...
  }
}
```

## 🔒 Production Safety

✅ **Implemented:**
- No hardcoded API keys (environment variables)
- Automatic ChromeDriver management (webdriver-manager)
- Async execution with threadpool (non-blocking)
- Request timeouts (30s default)
- Proper error handling and logging
- Resource cleanup (driver.quit() in finally blocks)
- Concurrency limits (ThreadPoolExecutor with max_workers=3)

## 📝 License

Part of the AuthentiChip backend system.

## 🤝 Support

For issues or questions, contact the development team.
