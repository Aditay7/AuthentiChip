import os
import json
import time
import re
import urllib.parse
import requests
import google.generativeai as genai

from fastapi import FastAPI, UploadFile, File, Form
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from fastapi.middleware.cors import CORSMiddleware
from collections import OrderedDict

# Load settings
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.core.config import get_settings

# ---------------------------------------------------
# GEMINI INIT
# ---------------------------------------------------
settings = get_settings()
if not settings.GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please add it to your .env file.")

genai.configure(api_key=settings.GEMINI_API_KEY)
GEMINI_MODEL = genai.GenerativeModel("gemini-2.5-flash")  # or "gemini-2.0-flash"

GEMINI_PROMPT = """
You are an expert IC datasheet analyzer with precision and focus.

CRITICAL INSTRUCTIONS:
1. Extract mechanical dimensions from the MAIN package specification table ONLY.
2. Return ONLY ONE JSON object (not an array, not multiple packages).
3. Extract the FIRST and PRIMARY package type mentioned in the datasheet.
4. Include ONLY the most relevant dimensions for that package.
5. All measurements MUST be in millimeters (mm).
6. Null means data not available - use null instead of empty string.
7. Return VALID JSON ONLY - no explanations, no comments, no markdown.
8. Do NOT extract data from multiple package types or comparison tables.

TASK:
From the IC datasheet, extract:
- Manufacturer name
- Full part numbers
- Allowed chip markings
- Package type (e.g., DIP-20, PDIP-16, SOIC-16, etc.)
- Mechanical dimensions for that SINGLE package:
  * body_length_min_mm, body_length_nom_mm, body_length_max_mm
  * body_width_min_mm, body_width_nom_mm, body_width_max_mm

Example output (EXACTLY this structure):
{
  "manufacturer": "Texas Instruments",
  "full_part_numbers": "SN74HCT257NE4",
  "allowed_markings": ["SN74HCT257N"],
  "package_type": "PDIP-16",
  "package_dimensions": {
    "body_length_min_mm": 18.92,
    "body_length_nom_mm": 19.305,
    "body_length_max_mm": 19.69,
    "body_width_min_mm": 6.1,
    "body_width_nom_mm": 6.35,
    "body_width_max_mm": 6.6
  }
}


STRICT RULE: Return only valid JSON. No explanations. One object only.
"""

# ---------------------------------------------------
# FASTAPI SETUP (COMMENTED OUT)
# ---------------------------------------------------
# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


def dedupe_json(data):
    """
    Recursively remove duplicate keys and normalize structure.
    Keeps the LAST value (Gemini's best guess).
    """
    if isinstance(data, dict):
        new = OrderedDict()
        for k, v in data.items():
            new[k] = dedupe_json(v)
        return dict(new)

    elif isinstance(data, list):
        return [dedupe_json(x) for x in data]

    return data


def extract_package_from_part_number(part_number):
    """
    Extract package type from part number.
    Examples: sn74hct257N -> PDIP-16, SN74HCT257D -> SOIC-16, etc.
    """
    part_upper = part_number.upper()
    
    # Common package suffixes mapping
    if 'N' in part_upper:
        return 'PDIP-16'
    elif 'D' in part_upper or 'DR' in part_upper or 'DT' in part_upper:
        return 'SOIC-16'
    elif 'NS' in part_upper:
        return 'SSOP-16'
    elif 'PW' in part_upper or 'PWR' in part_upper:
        return 'TSSOP-16'
    else:
        return None  # Return None if package cannot be determined


def filter_dimensions_by_package(dimensions, package_type):
    """
    Filter dimensions to show only specific package type.
    """
    if not package_type:
        return dimensions
    
    # If dimensions is a list (multiple package entries)
    if isinstance(dimensions, list):
        filtered_list = []
        for item in dimensions:
            if isinstance(item, dict) and item.get('package_type') == package_type:
                filtered_list.append(item)
        return filtered_list if filtered_list else dimensions
    
    # If dimensions is a dict with package_details
    if isinstance(dimensions, dict) and 'package_details' in dimensions:
        filtered = dimensions.copy()
        if package_type in dimensions.get('package_details', {}):
            filtered['package_details'] = {
                package_type: dimensions['package_details'][package_type]
            }
            if 'package_types' in filtered:
                filtered['package_types'] = [package_type]
        return filtered
    
    return dimensions


# ---------------------------------------------------
# SELENIUM DRIVER
# ---------------------------------------------------
def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    return webdriver.Chrome(options=options)


# ---------------------------------------------------
# SCRAPE DATASHEET PAGE LINKS
# ---------------------------------------------------
def scrape_pdf_pages(driver, chip):
    url = f"https://www.alldatasheet.com/view.jsp?Searchword={chip}"
    driver.get(url)
    time.sleep(2)

    links = []
    rows = driver.find_elements(By.CSS_SELECTOR, "tr.nv_td")

    for r in rows:
        try:
            href = r.find_element(By.CSS_SELECTOR, "td:nth-child(2) a").get_attribute("href")
            if href.startswith("//"):
                href = "https:" + href
            links.append(href)
        except:
            pass

    return links


# ---------------------------------------------------
# EXTRACT "DOWNLOAD DATASHEET" URL
# ---------------------------------------------------
def extract_download_link(driver, url):
    driver.get(url)
    time.sleep(2)
    try:
        link = driver.find_element(By.CSS_SELECTOR, "td#main_img a").get_attribute("href")
        if link.startswith("//"):
            link = "https:" + link
        return link
    except:
        return None


# ---------------------------------------------------
# EXTRACT REAL PDF URL FROM IFRAME
# ---------------------------------------------------
def extract_iframe_pdf(driver, download_url):
    """
    Extract PDF URL from iframe with improved error handling.
    Tries multiple methods to find the PDF link.
    """
    driver.get(download_url)
    time.sleep(3)  # Give more time for page to load
    
    try:
        # Method 1: Try to find iframe and get src
        try:
            iframe = driver.find_element(By.TAG_NAME, "iframe")
            src = iframe.get_attribute("src")
            if src:
                raw = src.split("file=")[1] if "file=" in src else src
                raw = raw.lstrip("/")
                raw = raw.replace(" ", "+")
                raw = urllib.parse.quote(raw, safe=":/+._-")
                if not raw.startswith("http"):
                    raw = "https://" + raw
                return raw
        except:
            pass
        
        # Method 2: Look for direct PDF download button/link
        try:
            pdf_links = driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")
            for link in pdf_links:
                href = link.get_attribute("href")
                if href and ".pdf" in href.lower():
                    if not href.startswith("http"):
                        href = "https://www.alldatasheet.com" + href
                    return href
        except:
            pass
        
        # Method 3: Check for embed tags
        try:
            embed = driver.find_element(By.TAG_NAME, "embed")
            src = embed.get_attribute("src")
            if src and ".pdf" in src.lower():
                if not src.startswith("http"):
                    src = "https://www.alldatasheet.com" + src
                return src
        except:
            pass
        
        # Method 4: Extract from page source
        try:
            page_source = driver.page_source
            if "file=" in page_source:
                import re
                match = re.search(r'file=([^"&\s]+)', page_source)
                if match:
                    raw = match.group(1)
                    raw = raw.lstrip("/")
                    raw = raw.replace(" ", "+")
                    raw = urllib.parse.quote(raw, safe=":/+._-")
                    if not raw.startswith("http"):
                        raw = "https://" + raw
                    return raw
        except:
            pass
        
        return None
        
    except Exception as e:
        print(f"Debug: {str(e)}")
        return None


# ---------------------------------------------------
# DOWNLOAD PDF
# ---------------------------------------------------
def download_pdf(url, path):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/pdf",
        "Referer": "https://www.alldatasheet.com/",
    }

    r = requests.get(url, headers=headers, stream=True)
    if r.status_code == 200:
        with open(path, "wb") as f:
            for chunk in r.iter_content(1024):
                if chunk:
                    f.write(chunk)
        return True
    return False


# ---------------------------------------------------
# GEMINI DIMENSION EXTRACTION
# ---------------------------------------------------
def extract_dimensions_with_gemini(pdf_bytes):
    response = GEMINI_MODEL.generate_content(
        [GEMINI_PROMPT, {"mime_type": "application/pdf", "data": pdf_bytes}]
    )

    text = response.text.strip()

    # Cleanup: remove markdown fences like ```json ... ```
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    # Cleanup: remove accidental backticks anywhere
    text = text.strip("`").strip()

    # Parse JSON
    try:
        parsed = json.loads(text)

        # Fix duplicate keys
        cleaned = dedupe_json(parsed)

        return cleaned

    except Exception as e:
        return {
            "error": "Gemini returned non-JSON",
            "cleaned_output": text,
            "exception": str(e)
        }


# ---------------------------------------------------
# MAIN SERVICE FUNCTION (FOR API)
# ---------------------------------------------------
def scrape_and_extract(ic_name, save_pdf=True):
    """
    Main service function: scrape datasheet and extract dimensions.
    Used by the FastAPI endpoints.
    """
    import os
    from pathlib import Path
    
    DOWNLOADS_DIR = Path("downloads")
    if save_pdf:
        DOWNLOADS_DIR.mkdir(exist_ok=True)
    
    driver = create_driver()
    
    try:
        # Step 1: Scrape datasheet pages
        pages = scrape_pdf_pages(driver, ic_name)
        if not pages:
            return {
                "error": "No datasheet found",
                "detail": f"Could not find any datasheets for {ic_name} on alldatasheet.com"
            }
        
        # Step 2: Extract download page link
        download_page = extract_download_link(driver, pages[0])
        if not download_page:
            return {
                "error": "Download link not found",
                "detail": "Could not extract download page link from datasheet page"
            }
        
        # Step 3: Extract real PDF URL from iframe
        real_pdf = extract_iframe_pdf(driver, download_page)
        if not real_pdf:
            return {
                "error": "PDF URL extraction failed",
                "detail": "Could not extract PDF URL from download page iframe"
            }
        
        # Step 4: Download PDF
        pdf_path = str(DOWNLOADS_DIR / f"{ic_name}.pdf") if save_pdf else f"temp_{ic_name}.pdf"
        if not download_pdf(real_pdf, pdf_path):
            return {
                "error": "PDF download failed",
                "detail": "Failed to download PDF from extracted URL"
            }
        
        # Step 5: Extract dimensions with Gemini
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        dimensions = extract_dimensions_with_gemini(pdf_bytes)
        
        # Clean up temp file if not saving
        if not save_pdf:
            try:
                os.remove(pdf_path)
            except:
                pass
        
        # Check if Gemini returned an error
        if "error" in dimensions:
            return {
                "error": "Gemini extraction failed",
                "detail": dimensions.get("error", "Unknown Gemini error"),
                "pdf_url": real_pdf
            }
        
        return {
            "chip": ic_name,
            "pdf_url": real_pdf,
            "dimensions": dimensions
        }
        
    except Exception as e:
        return {
            "error": "Extraction failed",
            "detail": str(e)
        }
    
    finally:
        driver.quit()



# ---------------------------------------------------
# API: SCRAPE + EXTRACT (FULL AUTOMATION) - COMMENTED OUT
# ---------------------------------------------------
# @app.get("/scrape-and-extract/{ic_name}")
# async def scrape_and_extract(ic_name: str):
#     driver = create_driver()
#
#     try:
#         # Step 1 → scrape alldatasheet for datasheet pages
#         pages = scrape_pdf_pages(driver, ic_name)
#         if not pages:
#             return {"error": f"No datasheet found for {ic_name}"}
#
#         # Step 2 → extract download page link
#         download_page = extract_download_link(driver, pages[0])
#         if not download_page:
#             return {"error": "Failed to find download link"}
#
#         # Step 3 → extract real PDF URL from iframe
#         real_pdf = extract_iframe_pdf(driver, download_page)
#         if not real_pdf:
#             return {"error": "Failed to extract PDF iframe URL"}
#
#         # Step 4 → download PDF
#         pdf_path = f"{ic_name}.pdf"
#         if not download_pdf(real_pdf, pdf_path):
#             return {"error": "Failed to download PDF"}
#
#         # Step 5 → send PDF to Gemini model
#         with open(pdf_path, "rb") as f:
#             pdf_bytes = f.read()
#
#         dimensions = extract_dimensions_with_gemini(pdf_bytes)
#
#         return {
#             "chip": ic_name,
#             "pdf_url": real_pdf,
#             "dimensions": dimensions
#         }
#
#     finally:
#         driver.quit()


# ---------------------------------------------------
# API: DIRECT PDF FILE UPLOAD - COMMENTED OUT
# ---------------------------------------------------
# @app.post("/extract/from-file")
# async def extract_from_file(pdf: UploadFile = File(...)):
#     pdf_bytes = await pdf.read()
#     dims = extract_dimensions_with_gemini(pdf_bytes)
#     return {"file": pdf.filename, "dimensions": dims}


# ---------------------------------------------------
# API: EXTRACT FROM URL - COMMENTED OUT
# ---------------------------------------------------
# @app.post("/extract/from-url")
# async def extract_from_url(pdf_url: str = Form(...)):
#     pdf_path = "temp.pdf"
#
#     ok = download_pdf(pdf_url, pdf_path)
#     if not ok:
#         return {"error": "Failed to download PDF"}
#
#     with open(pdf_path, "rb") as f:
#         pdf_bytes = f.read()
#
#     dims = extract_dimensions_with_gemini(pdf_bytes)
#     return {"pdf_url": pdf_url, "dimensions": dims}
#
#
# @app.get("/")
# def root():
#     return {"message": "Gemini IC dimension extractor is running!"}


# ---------------------------------------------------
# TERMINAL INPUT - MAIN EXECUTION
# ---------------------------------------------------
if __name__ == "__main__":
    print("\n" + "="*60)
    print("Gemini IC Dimension Extractor - Terminal Mode")
    print("="*60 + "\n")
    
    ic_name = input("Enter IC part number (e.g., SN74HCT257N): ").strip()
    
    if not ic_name:
        print("\n❌ Error: IC number cannot be empty!")
        exit(1)
    
    print(f"\n🔍 Searching for IC: {ic_name}...")
    print("⏳ This may take a moment...\n")
    
    driver = create_driver()
    
    try:
        # Step 1 → scrape alldatasheet for datasheet pages
        print("[Step 1] Scraping AllDataSheet...")
        pages = scrape_pdf_pages(driver, ic_name)
        if not pages:
            print(f"\n❌ Error: No datasheet found for {ic_name}")
            exit(1)
        print(f"✓ Found {len(pages)} datasheet(s)")
        
        # Step 2 → extract download page link
        print("\n[Step 2] Extracting download page link...")
        download_page = extract_download_link(driver, pages[0])
        if not download_page:
            print("\n❌ Error: Failed to find download link")
            exit(1)
        print("✓ Download page link found")
        
        # Step 3 → extract real PDF URL from iframe
        print("\n[Step 3] Extracting PDF URL from iframe...")
        real_pdf = extract_iframe_pdf(driver, download_page)
        if not real_pdf:
            print("\n❌ Error: Failed to extract PDF iframe URL")
            exit(1)
        print("✓ PDF URL extracted")
        
        # Step 4 → download PDF
        print("\n[Step 4] Downloading PDF...")
        pdf_path = f"{ic_name}.pdf"
        if not download_pdf(real_pdf, pdf_path):
            print("\n❌ Error: Failed to download PDF")
            exit(1)
        print(f"✓ PDF saved to {pdf_path}")
        
        # Step 5 → send PDF to Gemini model
        print("\n[Step 5] Analyzing with Gemini AI...")
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        dimensions = extract_dimensions_with_gemini(pdf_bytes)
        
        # Extract package type from part number
        package_type = extract_package_from_part_number(ic_name)
        
        # Filter dimensions if package type is identified
        if package_type:
            filtered_dimensions = filter_dimensions_by_package(dimensions, package_type)
            print(f"\n✓ Detected package: {package_type}")
        else:
            filtered_dimensions = dimensions
            print("\n⚠️  Could not determine package type from part number.")
            print("   Showing all available packages.")
        
        # Display results
        print("\n" + "="*60)
        print("📋 EXTRACTED DIMENSIONS")
        print("="*60)
        print(f"\nChip: {ic_name}")
        print(f"PDF URL: {real_pdf}\n")
        print(json.dumps(filtered_dimensions, indent=2))
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        exit(1)
    finally:
        driver.quit()