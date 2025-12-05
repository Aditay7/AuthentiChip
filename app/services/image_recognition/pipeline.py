import ollama
import json
import sys
import time
from pathlib import Path
from typing import Optional, List
from dataclasses import asdict

from app.models.ic_markings import ICMarkingData


def extract_text_from_image(image_path: str, model: str = "minicpm-v:8b") -> tuple[str, float]:
    """
    Extract text from an image using vision model
    
    Args:
        image_path: Path to the image file
        model: Ollama model to use
    
    Returns:
        Tuple of (extracted_text, inference_time)
    """
    if not Path(image_path).exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    print(f"🔍 Analyzing image: {image_path}")
    print(f"🤖 Using model: {model}")
    print("⏳ Processing...\n")
    
    start_time = time.time()
    
    # Optimized prompt for IC chip text extraction
    prompt = """Extract all text from this IC chip image. 
List each text element exactly as it appears, one per line.
Return ONLY the text, no explanations."""
    
    try:
        response = ollama.chat(
            model=model,
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [image_path]
            }]
        )
        
        extracted_text = response['message']['content'].strip()
        
        # Clean up XML tags if present
        extracted_text = extracted_text.replace('<doc>', '').replace('</doc>', '')
        extracted_text = extracted_text.strip()
        
        elapsed_time = time.time() - start_time
        
        return extracted_text, elapsed_time
        
    except Exception as e:
        raise RuntimeError(f"Error during text extraction: {str(e)}")


def parse_ic_markings(raw_text: str) -> ICMarkingData:
    """
    Parse raw OCR text into structured IC marking data.
    Tries to find a reasonable base part number like 'HT12D'
    even when OCR returns everything on a single line.
    """
    # Split into lines and clean
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

    if not lines:
        return ICMarkingData()

    manufacturer: Optional[str] = None
    base_part_number: Optional[str] = None
    full_part_numbers: List[str] = []
    allowed_markings: List[str] = []

    # Keep original lines as allowed markings
    allowed_markings.extend(lines)

    # Common manufacturer strings (extend as you like)
    common_manufacturers = {
        'CMD', 'TI', 'AMD', 'NXP', 'ST', 'ON', 'PHILIPS', 'INTEL',
        'ATMEL', 'MAXIM', 'ADI', 'TL', 'HA', 'AN', 'ID',
        'HOLTEK', 'HT'  # added to catch Holtek / HT series
    }

    # First pass: go through every line and every token
    for i, line in enumerate(lines):
        # Manufacturer guess – *short* identifiers or known names
        upper_line = line.upper()
        if (upper_line in common_manufacturers or len(line) <= 4) and manufacturer is None:
            manufacturer = line

        # Token-level parsing
        for raw_token in line.split():
            token = raw_token.strip(",:;#-_")  # remove common junk
            if not token:
                continue

            upper_token = token.upper()

            # If token itself looks like a manufacturer
            if upper_token in common_manufacturers and manufacturer is None:
                manufacturer = token
                continue

            # Detect part-number-like tokens (letters + digits)
            has_letter = any(c.isalpha() for c in token)
            has_digit = any(c.isdigit() for c in token)

            if has_letter and has_digit and len(token) >= 4:
                if token not in full_part_numbers:
                    full_part_numbers.append(token)

    # Choose base_part_number as the shortest part-number-like token
    if full_part_numbers:
        base_part_number = min(full_part_numbers, key=len)

    # If still no manufacturer, don't force it to the whole line;
    # leave as None or try a very weak guess:
    if manufacturer is None and lines:
        # only use first line as manufacturer if it's very short
        if len(lines[0]) <= 6:
            manufacturer = lines[0]

    return ICMarkingData(
        manufacturer=manufacturer,
        base_part_number=base_part_number,
        full_part_numbers=full_part_numbers if full_part_numbers else None,
        allowed_markings=allowed_markings if allowed_markings else None
    )



def main():
    """Main function to run text extraction and parsing"""
    
    # Default image path
    default_image = "image.jpg"
    
    # Get image path from command line or use default
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = default_image
    
    try:
        # Extract text
        raw_text, inference_time = extract_text_from_image(image_path)
        
        # Parse into structured data
        ic_data = parse_ic_markings(raw_text)
        
        # Display results
        print("=" * 60)
        print("📝 RAW OCR TEXT:")
        print("=" * 60)
        print(raw_text)
        print("=" * 60)
        print("\n📦 STRUCTURED IC MARKING DATA:")
        print("=" * 60)
        print(json.dumps(asdict(ic_data), indent=2))
        print("=" * 60)
        print(f"\n⏱️  Inference time: {inference_time:.2f} seconds")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print(f"\nUsage: python main.py [image_path]")
        print(f"Example: python main.py chip.jpg")
        sys.exit(1)
        
    except RuntimeError as e:
        print(f"❌ Error: {e}")
        print("\nMake sure Ollama is running and the model is downloaded.")
        sys.exit(1)


if __name__ == "__main__":
    main()
