#!/usr/bin/env python3
"""
Smart Crop Script
Handles intelligent IC cropping and rotation from two sources:
1. Raspberry Pi Endpoint (GET request)
2. Local Folder (Recursive processing)
"""

import cv2
import numpy as np
import argparse
import os
import requests
import shutil
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional, List, Dict

# --- Core Logic from ICDimensionAnalyzer (Refactored) ---

class SmartCropper:
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode

    def process_image(self, img: np.ndarray) -> Tuple[Optional[np.ndarray], Dict]:
        """
        Detects IC, rotates, and crops the image.
        Returns: (cropped_image, stats_dict)
        """
        if img is None:
            return None, {"error": "Image is None"}

        # 1. Find IC Body Contour
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        kernel = np.ones((5, 5), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=3)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)
        
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None, {"error": "No contours found"}
            
        img_area = img.shape[0] * img.shape[1]
        valid_contours = [c for c in contours if 0.01 * img_area < cv2.contourArea(c) < 0.9 * img_area]
        
        if not valid_contours:
            return None, {"error": "No valid IC contours found"}
            
        ic_contour = max(valid_contours, key=cv2.contourArea)
        
        # 2. Determine Rotation and Dimensions
        rect = cv2.minAreaRect(ic_contour)
        center, (w, h), angle = rect
        
        # Ensure width > height for consistency
        if w < h:
            w, h = h, w
            angle += 90
            
        # 3. Rotate Image
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated_img = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_CUBIC)
        rotated_mask = cv2.warpAffine(binary, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_NEAREST)
        
        # 4. Refine Crop (Projection Profile Logic Simplified)
        # Extract initial ROI
        pad = 50
        roi_w, roi_h = int(w + pad*2), int(h + pad*2)
        roi = cv2.getRectSubPix(rotated_mask, (roi_w, roi_h), center)
        
        if roi is None:
             return None, {"error": "ROI extraction failed"}

        row_sum = np.sum(roi, axis=1) / 255.0
        col_sum = np.sum(roi, axis=0) / 255.0
        
        def get_range(profile, threshold_ratio):
            max_val = np.max(profile)
            if max_val == 0: return 0, 0
            indices = np.where(profile > max_val * threshold_ratio)[0]
            if len(indices) > 0:
                return indices[0], indices[-1]
            return 0, 0

        # Heuristic for thresholds (simplified from original for robustness)
        # Using a safe default that generally works for body detection
        thresh_h = 0.85 
        thresh_w = 0.80
        
        y_start, y_end = get_range(row_sum, thresh_h)
        x_start, x_end = get_range(col_sum, thresh_w)
        
        final_h = y_end - y_start
        final_w = x_end - x_start
        
        if final_h < 10 or final_w < 10:
             return None, {"error": "Calculated dimensions too small"}

        # Calculate crop center in ROI coordinates
        crop_center_y_roi = (y_start + y_end) / 2
        crop_center_x_roi = (x_start + x_end) / 2
        
        # Shift from ROI center
        roi_center_y = roi_h // 2
        roi_center_x = roi_w // 2
        
        shift_x = crop_center_x_roi - roi_center_x
        shift_y = crop_center_y_roi - roi_center_y
        
        # New center in the rotated image
        new_center_x = center[0] + (shift_x * np.cos(np.radians(0)) - shift_y * np.sin(np.radians(0))) # Already in rotated frame effectively for crop
        new_center_y = center[1] + (shift_x * np.sin(np.radians(0)) + shift_y * np.cos(np.radians(0)))
        
        # Actually, since we already have the rotated image, we can just crop from it using getRectSubPix
        # But getRectSubPix needs the center in the image coordinates.
        # The 'center' variable is the center of rotation.
        # We need to adjust 'center' by the shift found in the ROI.
        
        # Let's map the shift back to the rotated image space.
        # The ROI was extracted from 'rotated_mask' at 'center'.
        # So (roi_center_x, roi_center_y) corresponds to 'center' in 'rotated_mask'.
        # So (crop_center_x_roi, crop_center_y_roi) corresponds to:
        final_center_x = center[0] + shift_x
        final_center_y = center[1] + shift_y
        
        final_crop = cv2.getRectSubPix(rotated_img, (int(final_w), int(final_h)), (final_center_x, final_center_y))
        
        return final_crop, {
            "width": final_w,
            "height": final_h,
            "angle": angle,
            "original_width": w,
            "original_height": h
        }

# --- Mode Handlers ---

def handle_pi_mode(url: str, output_dir: str):
    print(f"--- Pi Mode: Fetching from {url} ---")
    try:
        # In a real scenario, we'd do: response = requests.get(url, stream=True).raw
        # For now, let's assume the URL returns an image directly
        print(f"GET {url}...")
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if img is None:
                print("Error: Could not decode image from response.")
                return

            cropper = SmartCropper()
            cropped_img, stats = cropper.process_image(img)
            
            if cropped_img is not None:
                os.makedirs(output_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"pi_capture_{timestamp}.jpg"
                save_path = os.path.join(output_dir, filename)
                cv2.imwrite(save_path, cropped_img)
                
                print(f"\nSUCCESS: Image saved to {save_path}")
                print(f"Dimensions: {stats['width']:.2f} x {stats['height']:.2f} pixels")
                print(f"Angle Corrected: {stats['angle']:.2f} degrees")
            else:
                print(f"Error processing image: {stats.get('error')}")
        else:
            print(f"Error: Failed to fetch image. Status code: {response.status_code}")
            
    except Exception as e:
        print(f"Exception in Pi Mode: {e}")

def handle_folder_mode(input_dir: str):
    print(f"--- Folder Mode: Processing {input_dir} ---")
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return

    parent_dir = input_path.parent
    output_dir_name = f"{input_path.name}-cropped"
    output_path = parent_dir / output_dir_name
    
    dims_file_path = output_path / "ic_dimensions.txt"
    
    print(f"Output Directory: {output_path}")
    
    cropper = SmartCropper()
    
    # Prepare dimensions file
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True)
    
    with open(dims_file_path, "w") as f:
        f.write("Filename, Width, Height, Angle\n")
        
    count = 0
    success_count = 0
    
    for file_path in input_path.rglob("*"):
        if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            count += 1
            # Calculate relative path to maintain structure
            rel_path = file_path.relative_to(input_path)
            dest_path = output_path / rel_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"Processing: {rel_path}...", end="", flush=True)
            
            img = cv2.imread(str(file_path))
            cropped_img, stats = cropper.process_image(img)
            
            if cropped_img is not None:
                cv2.imwrite(str(dest_path), cropped_img)
                
                with open(dims_file_path, "a") as f:
                    f.write(f"{rel_path}, {stats['width']:.2f}, {stats['height']:.2f}, {stats['angle']:.2f}\n")
                
                print(f" Done. ({stats['width']:.1f}x{stats['height']:.1f})")
                success_count += 1
            else:
                print(f" Failed. ({stats.get('error')})")
                # Optionally copy original if failed? Or just skip. 
                # User said "re organise by cloning the folder", implying we might want to keep failed ones too?
                # "crop them to the bounding box... in case of from folder: dims of all ics to be added"
                # I'll skip saving failed crops to avoid confusion, but maybe log it.
                
    print(f"\nProcessing Complete.")
    print(f"Total Images: {count}")
    print(f"Successfully Cropped: {success_count}")
    print(f"Dimensions saved to: {dims_file_path}")

def main():
    parser = argparse.ArgumentParser(description="Smart IC Crop & Rotate")
    subparsers = parser.add_subparsers(dest="mode", help="Mode of operation")
    
    # Pi Mode
    pi_parser = subparsers.add_parser("pi", help="Get image from Raspberry Pi Endpoint")
    pi_parser.add_argument("--url", required=True, help="URL of the image endpoint")
    pi_parser.add_argument("--output", default="pi-crop-imgs", help="Output directory for cropped images")
    
    # Folder Mode
    folder_parser = subparsers.add_parser("folder", help="Process images from a folder recursively")
    folder_parser.add_argument("--input", required=True, help="Input folder path")
    
    args = parser.parse_args()
    
    if args.mode == "pi":
        handle_pi_mode(args.url, args.output)
    elif args.mode == "folder":
        handle_folder_mode(args.input)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
