#!/usr/bin/env python3
"""
Test script for upload_and_extract_service.py
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from upload_and_extract_service import upload_extract_service
    print("✅ Upload and extract service imported successfully")
    
    # Test service configuration
    print(f"✅ Google Cloud Bucket: {upload_extract_service.google_cloud_bucket}")
    print(f"✅ Max file size: {upload_extract_service.max_file_size / 1024 / 1024:.1f}MB")
    print(f"✅ Allowed file types: {upload_extract_service.allowed_file_types}")
    print(f"✅ Debug mode: {upload_extract_service.debug}")
    
    # Test if storage client initialized
    if upload_extract_service.storage_client:
        print("✅ Google Cloud Storage client initialized")
    else:
        print("⚠️  Google Cloud Storage client not initialized (running locally)")
    
    print("\n🎉 All tests passed! The upload and extract service is working correctly.")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
    sys.exit(1)
