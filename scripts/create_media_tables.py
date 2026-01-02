#!/usr/bin/env python3
# Made by Mister 💛

"""
Migration script to create media tables for Advanced Media Simulation Mode.
Run this script manually to initialize the media database.

Usage:
    python scripts/create_media_tables.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.media_tables import MediaDatabase


def main():
    print("=" * 50)
    print("Media Tables Migration Script")
    print("Made by Mister 💛")
    print("=" * 50)
    
    try:
        db = MediaDatabase()
        print("\n✅ Media database tables created successfully!")
        print(f"   Database path: {db.db_path}")
        print("\nTables created:")
        print("   - media_channels")
        print("   - media_categories")
        print("   - media_logs")
        print("\nYou can now use /media_setup in the bot to manage media channels.")
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
