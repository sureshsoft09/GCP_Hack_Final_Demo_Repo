#!/usr/bin/env python3
"""
Test script for the Backend API service
Tests all endpoints to ensure proper communication with Agents API
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any

# Configuration
BACKEND_URL = "http://localhost:8083"
AGENTS_URL = "http://localhost:8082"

def test_endpoint(endpoint: str, payload: Dict[str, Any]) -> None:
    """Test a specific endpoint with given payload"""
    print(f"\n🧪 Testing {endpoint}...")
    
    try:
        # Prepare the request
        url = f"{BACKEND_URL}/{endpoint}"
        data = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(
            url, 
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            method='POST'
        )
        
        # Make the request
        with urllib.request.urlopen(req, timeout=30) as response:
            print(f"   Status: {response.status}")
            
            if response.status == 200:
                result_data = response.read().decode('utf-8')
                result = json.loads(result_data)
                response_text = result.get('response', 'No response field')
                print(f"   ✅ Success: {response_text}...")
            else:
                print(f"   ❌ Error: Status {response.status}")
                
    except urllib.error.HTTPError as e:
        print(f"   ❌ HTTP Error {e.code}: {e.reason}")
        if e.code == 422:
            try:
                error_details = e.read().decode('utf-8')
                print(f"   📋 Error Details: {error_details}")
            except:
                print("   📋 Could not read error details")
    except urllib.error.URLError as e:
        print(f"   💥 URL Error: {e.reason}")
    except Exception as e:
        print(f"   💥 Exception: {str(e)}")

def check_health(url: str, service_name: str) -> bool:
    """Check if a service is running"""
    try:
        req = urllib.request.Request(f"{url}/health", method='GET')
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                result_data = response.read().decode('utf-8')
                health = json.loads(result_data)
                print(f"✅ {service_name} Health: {health}")
                return True
            else:
                print(f"❌ {service_name} health check failed: {response.status}")
                return False
    except Exception as e:
        print(f"💥 Cannot connect to {service_name}: {e}")
        return False

def main():
    """Run all backend endpoint tests"""
    print("🚀 Starting Backend API Tests")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Agents URL: {AGENTS_URL}")
    
    # Check if backend is running
    if not check_health(BACKEND_URL, "Backend"):
        print("Make sure the backend is running on http://localhost:8083")
        return
    
    # Test payloads for each endpoint
    test_cases = [
        {
            "endpoint": "generate_test_cases",
            "payload": {
                "prompt": "Generate test cases for patient login functionality"
            }
        },
        {
            "endpoint": "enhance_test_cases",
            "payload": {
                "prompt": "Enhance test cases for user authentication with edge cases"
            }
        },
        {
            "endpoint": "migration_test_cases",
            "payload": {
                "prompt": "Create migration test cases for database schema changes"
            }
        },
        {
            "endpoint": "clarification_chat",
            "payload": {
                "prompt": "What are the best practices for API testing?"
            }
        }
    ]
    
    # Test all endpoints
    for test_case in test_cases:
        test_endpoint(test_case["endpoint"], test_case["payload"])
        print("   Waiting 2 seconds before next test...")
        import time
        time.sleep(2)  # Brief pause between tests
    
    print("\n🏁 Backend API Tests Completed!")

if __name__ == "__main__":
    main()
