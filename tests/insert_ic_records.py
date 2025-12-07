#!/usr/bin/env python3
"""
Script to insert IC records into the database.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings
from app.repositories.ic_repository import ICRepository


# IC data to insert
IC_DATA = [
    {
        "manufacturer": "Atmel",
        "full_part_number": "AT89S52-24PC",
        "allowed_markings": ["AT89S52", "89S52", "ATMEL"],
        "package_type": "PDIP-40 (0.600\" wide)",
        "package_dimensions": {
            "body_length_min_mm": 51.8,
            "body_length_nom_mm": None,
            "body_length_max_mm": 52.6,
            "body_width_min_mm": 13.5,
            "body_width_nom_mm": None,
            "body_width_max_mm": 14.4
        }
    },
    {
        "manufacturer": "Atmel",
        "full_part_number": "AT89S52-24PU",
        "allowed_markings": ["AT89S52", "89S52", "ATMEL"],
        "package_type": "PDIP-40 (0.600\" wide)",
        "package_dimensions": {
            "body_length_min_mm": 52.07,
            "body_length_nom_mm": None,
            "body_length_max_mm": 52.57,
            "body_width_min_mm": 13.46,
            "body_width_nom_mm": None,
            "body_width_max_mm": 13.97
        }
    },
    {
        "manufacturer": "Atmel",
        "full_part_number": "ATMEGA16A-PU",
        "allowed_markings": ["ATMEGA16A"],
        "package_type": "PDIP-40 (0.600\" wide)",
        "package_dimensions": {
            "body_length_min_mm": 52.07,
            "body_length_nom_mm": None,
            "body_length_max_mm": 52.57,
            "body_width_min_mm": 13.46,
            "body_width_nom_mm": None,
            "body_width_max_mm": 13.97
        }
    },
    {
        "manufacturer": "Fairchild/ON Semiconductor",
        "full_part_number": "MM74HC221AN",
        "allowed_markings": ["MM74HC221AN", "MC74HC221AN", "74HC221", "HC221"],
        "package_type": "PDIP-16",
        "package_dimensions": {
            "body_length_min_mm": 18.80,
            "body_length_nom_mm": None,
            "body_length_max_mm": 19.81,
            "body_width_min_mm": 6.10,
            "body_width_nom_mm": 6.35,
            "body_width_max_mm": 6.60
        }
    },
    {
        "manufacturer": "Motorola/ON Semiconductor",
        "full_part_number": "SN74LS164N",
        "allowed_markings": ["SN74LS164N", "74LS164", "LS164", "18419"],
        "package_type": "PDIP-14 (N Suffix)",
        "package_dimensions": {
            "body_length_min_mm": 18.16,
            "body_length_nom_mm": None,
            "body_length_max_mm": 18.80,
            "body_width_min_mm": 6.10,
            "body_width_nom_mm": None,
            "body_width_max_mm": 6.60
        }
    },
    {
        "manufacturer": "Motorola/ON Semiconductor",
        "full_part_number": "SN74LS164D",
        "allowed_markings": ["SN74LS164D", "74LS164", "LS164"],
        "package_type": "SOIC-14 (D Suffix)",
        "package_dimensions": {
            "body_length_min_mm": 8.55,
            "body_length_nom_mm": None,
            "body_length_max_mm": 8.75,
            "body_width_min_mm": 3.80,
            "body_width_nom_mm": None,
            "body_width_max_mm": 4.00
        }
    }
]


async def insert_ic_records():
    """Insert IC records into the database."""
    settings = get_settings()
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    
    # Create repository
    ic_repo = ICRepository(db)
    
    print("=" * 70)
    print("📥 Inserting IC Records into Database")
    print("=" * 70)
    
    created_count = 0
    
    for idx, ic_data in enumerate(IC_DATA, 1):
        try:
            # Create IC record
            result = await ic_repo.create(ic_data)
            created_count += 1
            
            print(f"\n✅ [{idx}/6] Created: {ic_data['manufacturer']}")
            print(f"   Part Number: {ic_data['full_part_number']}")
            print(f"   Package: {ic_data['package_type']}")
            print(f"   ID: {result['_id']}")
            
        except Exception as e:
            print(f"\n❌ [{idx}/6] Failed to create {ic_data['full_part_number']}: {e}")
    
    print("\n" + "=" * 70)
    print(f"✨ Successfully created {created_count}/{len(IC_DATA)} IC records")
    print("=" * 70)
    
    # Verify by listing all records
    print("\n" + "=" * 70)
    print("🔍 Verifying Database Contents")
    print("=" * 70)
    
    all_records = await ic_repo.list(limit=100)
    print(f"\n📊 Total IC records in database: {len(all_records)}\n")
    
    for idx, record in enumerate(all_records, 1):
        print(f"{idx}. {record['manufacturer']} - {record['full_part_number']}")
    
    print("\n" + "=" * 70)
    
    # Close connection
    client.close()


async def main():
    """Main function."""
    try:
        await insert_ic_records()
        print("\n✅ Database insertion completed successfully!\n")
    except Exception as e:
        print(f"\n❌ Error during database insertion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
