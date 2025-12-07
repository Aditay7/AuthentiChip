#!/usr/bin/env python3
"""
Test script to seed IC database with mock data.
This script creates 10 sample IC records in the database.

Usage:
    python tests/test_ic_database_seed.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings
from app.repositories.ic_repository import ICRepository


# Mock IC data - 10 different ICs
MOCK_IC_DATA = [
    {
        "manufacturer": "Texas Instruments",
        "full_part_number": "LM358N",
        "allowed_markings": ["LM358", "358N", "TI"],
        "package_type": "SOIC-8",
        "package_dimensions": {
            "body_length_min_mm": 4.8,
            "body_length_nom_mm": 5.0,
            "body_length_max_mm": 5.2,
            "body_width_min_mm": 3.8,
            "body_width_nom_mm": 4.0,
            "body_width_max_mm": 4.2
        },
        "image_data": {
            "original_image_path": None,
            "cropped_image_path": None,
            "content_type": "image/jpeg"
        },
        "dimensions_match": True,
        "texture_model_confidence_score": 87,
        "overall_confidence_score": 92
    },
    {
        "manufacturer": "STMicroelectronics",
        "full_part_number": "STM32F103C8T6",
        "allowed_markings": ["STM32F103", "STM32", "ST"],
        "package_type": "LQFP-48",
        "package_dimensions": {
            "body_length_min_mm": 6.8,
            "body_length_nom_mm": 7.0,
            "body_length_max_mm": 7.2,
            "body_width_min_mm": 6.8,
            "body_width_nom_mm": 7.0,
            "body_width_max_mm": 7.2
        },
        "image_data": {
            "original_image_path": None,
            "cropped_image_path": None,
            "content_type": "image/jpeg"
        },
        "dimensions_match": True,
        "texture_model_confidence_score": 91,
        "overall_confidence_score": 94
    },
    {
        "manufacturer": "Holtek",
        "full_part_number": "HT12D",
        "allowed_markings": ["HT12D", "12D", "HOLTEK"],
        "package_type": "DIP-18",
        "package_dimensions": {
            "body_length_min_mm": 22.5,
            "body_length_nom_mm": 22.86,
            "body_length_max_mm": 23.2,
            "body_width_min_mm": 6.0,
            "body_width_nom_mm": 6.35,
            "body_width_max_mm": 6.7
        },
        "image_data": {
            "original_image_path": None,
            "cropped_image_path": None,
            "content_type": "image/jpeg"
        },
        "dimensions_match": False,
        "texture_model_confidence_score": 78,
        "overall_confidence_score": 81
    },
    {
        "manufacturer": "NXP Semiconductors",
        "full_part_number": "74HC595N",
        "allowed_markings": ["74HC595", "HC595", "NXP"],
        "package_type": "DIP-16",
        "package_dimensions": {
            "body_length_min_mm": 18.9,
            "body_length_nom_mm": 19.3,
            "body_length_max_mm": 19.7,
            "body_width_min_mm": 6.1,
            "body_width_nom_mm": 6.35,
            "body_width_max_mm": 6.6
        },
        "image_data": {
            "original_image_path": None,
            "cropped_image_path": None,
            "content_type": "image/jpeg"
        },
        "dimensions_match": True,
        "texture_model_confidence_score": 95,
        "overall_confidence_score": 96
    },
    {
        "manufacturer": "Atmel",
        "full_part_number": "ATMEGA328P-PU",
        "allowed_markings": ["ATMEGA328P", "328P", "ATMEL"],
        "package_type": "DIP-28",
        "package_dimensions": {
            "body_length_min_mm": 34.5,
            "body_length_nom_mm": 35.0,
            "body_length_max_mm": 35.5,
            "body_width_min_mm": 7.4,
            "body_width_nom_mm": 7.62,
            "body_width_max_mm": 7.9
        },
        "image_data": {
            "original_image_path": None,
            "cropped_image_path": None,
            "content_type": "image/jpeg"
        },
        "dimensions_match": True,
        "texture_model_confidence_score": 89,
        "overall_confidence_score": 90
    },
    {
        "manufacturer": "Analog Devices",
        "full_part_number": "AD8232ACPZ",
        "allowed_markings": ["AD8232", "8232", "ADI"],
        "package_type": "LFCSP-20",
        "package_dimensions": {
            "body_length_min_mm": 3.9,
            "body_length_nom_mm": 4.0,
            "body_length_max_mm": 4.1,
            "body_width_min_mm": 3.9,
            "body_width_nom_mm": 4.0,
            "body_width_max_mm": 4.1
        },
        "image_data": {
            "original_image_path": None,
            "cropped_image_path": None,
            "content_type": "image/jpeg"
        },
        "dimensions_match": True,
        "texture_model_confidence_score": 93,
        "overall_confidence_score": 95
    },
    {
        "manufacturer": "Maxim Integrated",
        "full_part_number": "MAX232CPE",
        "allowed_markings": ["MAX232", "232", "MAXIM"],
        "package_type": "DIP-16",
        "package_dimensions": {
            "body_length_min_mm": 18.9,
            "body_length_nom_mm": 19.3,
            "body_length_max_mm": 19.7,
            "body_width_min_mm": 6.1,
            "body_width_nom_mm": 6.35,
            "body_width_max_mm": 6.6
        },
        "image_data": {
            "original_image_path": None,
            "cropped_image_path": None,
            "content_type": "image/jpeg"
        },
        "dimensions_match": False,
        "texture_model_confidence_score": 72,
        "overall_confidence_score": 75
    },
    {
        "manufacturer": "ON Semiconductor",
        "full_part_number": "LM7805CT",
        "allowed_markings": ["LM7805", "7805", "ON"],
        "package_type": "TO-220",
        "package_dimensions": {
            "body_length_min_mm": 9.8,
            "body_length_nom_mm": 10.0,
            "body_length_max_mm": 10.2,
            "body_width_min_mm": 4.3,
            "body_width_nom_mm": 4.5,
            "body_width_max_mm": 4.7
        },
        "image_data": {
            "original_image_path": None,
            "cropped_image_path": None,
            "content_type": "image/jpeg"
        },
        "dimensions_match": True,
        "texture_model_confidence_score": 85,
        "overall_confidence_score": 88
    },
    {
        "manufacturer": "Intel",
        "full_part_number": "AT89C51",
        "allowed_markings": ["8051", "89C51", "INTEL"],
        "package_type": "DIP-40",
        "package_dimensions": {
            "body_length_min_mm": 50.5,
            "body_length_nom_mm": 51.0,
            "body_length_max_mm": 51.5,
            "body_width_min_mm": 15.0,
            "body_width_nom_mm": 15.24,
            "body_width_max_mm": 15.5
        },
        "image_data": {
            "original_image_path": None,
            "cropped_image_path": None,
            "content_type": "image/jpeg"
        },
        "dimensions_match": True,
        "texture_model_confidence_score": 80,
        "overall_confidence_score": 83
    },
    {
        "manufacturer": "Microchip",
        "full_part_number": "PIC16F877A-I/P",
        "allowed_markings": ["PIC16F877A", "16F877A", "MCHP"],
        "package_type": "DIP-40",
        "package_dimensions": {
            "body_length_min_mm": 50.5,
            "body_length_nom_mm": 51.0,
            "body_length_max_mm": 51.5,
            "body_width_min_mm": 15.0,
            "body_width_nom_mm": 15.24,
            "body_width_max_mm": 15.5
        },
        "image_data": {
            "original_image_path": None,
            "cropped_image_path": None,
            "content_type": "image/jpeg"
        },
        "dimensions_match": True,
        "texture_model_confidence_score": 88,
        "overall_confidence_score": 91
    }
]


async def seed_ic_database():
    """Seed the IC database with mock data."""
    settings = get_settings()
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    
    # Create repository
    ic_repo = ICRepository(db)
    
    print("=" * 60)
    print("🌱 Seeding IC Database with Mock Data")
    print("=" * 60)
    
    created_count = 0
    
    for idx, ic_data in enumerate(MOCK_IC_DATA, 1):
        try:
            # Create IC record
            result = await ic_repo.create(ic_data)
            created_count += 1
            
            print(f"\n✅ [{idx}/10] Created: {ic_data['manufacturer']} - {ic_data['full_part_number']}")
            print(f"   📦 Package: {ic_data['package_type']}")
            print(f"   🆔 ID: {result['_id']}")
            print(f"   📊 Confidence: {ic_data['overall_confidence_score']}%")
            
        except Exception as e:
            print(f"\n❌ [{idx}/10] Failed to create {ic_data['full_part_number']}: {e}")
    
    print("\n" + "=" * 60)
    print(f"✨ Successfully created {created_count}/{len(MOCK_IC_DATA)} IC records")
    print("=" * 60)
    
    # Close connection
    client.close()


async def verify_seeded_data():
    """Verify the seeded data by listing all records."""
    settings = get_settings()
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    
    # Create repository
    ic_repo = ICRepository(db)
    
    print("\n" + "=" * 60)
    print("🔍 Verifying Seeded Data")
    print("=" * 60)
    
    # List all records
    records = await ic_repo.list(limit=100)
    
    print(f"\n📊 Total IC records in database: {len(records)}")
    print("\nRecords:")
    print("-" * 60)
    
    for idx, record in enumerate(records, 1):
        print(f"{idx}. {record['manufacturer']} - {record.get('full_part_number', 'N/A')}")
        print(f"   Package: {record['package_type']}")
        print(f"   ID: {record['_id']}")
        print(f"   Confidence: {record.get('overall_confidence_score', 'N/A')}%")
        print()
    
    # Close connection
    client.close()


async def main():
    """Main function to run the seed script."""
    try:
        # Seed the database
        await seed_ic_database()
        
        # Verify the seeded data
        await verify_seeded_data()
        
        print("\n✅ Database seeding completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during database seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
