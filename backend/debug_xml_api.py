#!/usr/bin/env python3
"""
Debug script for NYC Checkbook XML API
Examines raw responses to understand the API behavior
"""

import asyncio
import httpx
from jinja2 import Template

# Your App Token
APP_TOKEN = "2UYrUskVvUcZM1VR5e06dvfV"
API_URL = "https://www.checkbooknyc.com/api"

# Simple XML template
CONTRACT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<request>
  <type_of_data>Contracts</type_of_data>
  <records_from>1</records_from>
  <max_records>5</max_records>
</request>"""

print("🔍 DEBUG: NYC Checkbook XML API")
print("=" * 50)
print(f"API URL: {API_URL}")
print(f"App Token: {APP_TOKEN}")
print()

async def debug_api():
    """Debug the API response"""
    
    # Render XML template
    template = Template(CONTRACT_XML)
    xml_body = template.render()
    
    print("📤 XML Request Body:")
    print(xml_body)
    print()
    
    # Headers
    headers = {
        'Content-Type': 'application/xml',
        'X-App-Token': APP_TOKEN,
        'User-Agent': 'Vetting-Intelligence-Debug/1.0'
    }
    
    print("📤 Request Headers:")
    for key, value in headers.items():
        if key == 'X-App-Token':
            print(f"  {key}: {value[:8]}...{value[-8:]}")  # Partially hide token
        else:
            print(f"  {key}: {value}")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(API_URL, headers=headers, content=xml_body)
            
            print("📥 Response Details:")
            print(f"  Status Code: {response.status_code}")
            print(f"  Status Reason: {response.reason_phrase}")
            print()
            
            print("📥 Response Headers:")
            for key, value in response.headers.items():
                print(f"  {key}: {value}")
            print()
            
            print("📥 Response Body:")
            response_text = response.text
            print(f"  Length: {len(response_text)} characters")
            print(f"  Content Type: {response.headers.get('content-type', 'Unknown')}")
            
            if response_text:
                print(f"  Raw Content: {repr(response_text)}")
                print(f"  Pretty Content:")
                print(f"    {response_text}")
            else:
                print("  ⚠️  Response body is EMPTY")
            
            print()
            
            # Try to understand what went wrong
            if response.status_code == 200 and not response_text:
                print("🔍 ANALYSIS:")
                print("  • Status 200 (OK) but empty response")
                print("  • This could mean:")
                print("    - API processed request but found no matching data")
                print("    - API returned empty result set")
                print("    - Request format might not match expected schema")
                print("    - Authentication may have failed silently")
            elif response.status_code != 200:
                print("🔍 ANALYSIS:")
                print(f"  • HTTP Error {response.status_code}")
                print("  • This could mean:")
                print("    - Invalid API endpoint")
                print("    - Authentication failure")
                print("    - Invalid request format")
                print("    - API temporarily unavailable")
            else:
                print("🔍 ANALYSIS:")
                print("  • Received response content - need to examine format")
                
    except Exception as e:
        print(f"❌ Request Exception: {e}")
        print(f"   Exception type: {type(e).__name__}")

# Also test with different request formats
async def test_alternative_formats():
    """Test alternative request formats"""
    
    print("\n" + "=" * 50)
    print("🧪 TESTING ALTERNATIVE FORMATS")
    print("=" * 50)
    
    # Test 1: Without search criteria
    alt_xml_1 = """<?xml version="1.0" encoding="UTF-8"?>
<request>
  <type_of_data>Contracts</type_of_data>
  <records_from>1</records_from>
  <max_records>5</max_records>
</request>"""
    
    print("\n1. Testing without search criteria...")
    await test_format("No Search Criteria", alt_xml_1)
    
    # Test 2: Different type_of_data values
    alt_xml_2 = """<?xml version="1.0" encoding="UTF-8"?>
<request>
  <type_of_data>contracts</type_of_data>
  <records_from>1</records_from>
  <max_records>5</max_records>
</request>"""
    
    print("\n2. Testing lowercase type_of_data...")
    await test_format("Lowercase", alt_xml_2)
    
    # Test 3: Different structure
    alt_xml_3 = """<request>
  <type_of_data>Contracts</type_of_data>
  <records_from>1</records_from>
  <max_records>5</max_records>
</request>"""
    
    print("\n3. Testing without XML declaration...")
    await test_format("No XML Declaration", alt_xml_3)

async def test_format(format_name, xml_body):
    """Test a specific XML format"""
    headers = {
        'Content-Type': 'application/xml',
        'X-App-Token': APP_TOKEN,
        'User-Agent': 'Vetting-Intelligence-Debug/1.0'
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(API_URL, headers=headers, content=xml_body)
            
            print(f"  Status: {response.status_code}")
            if response.text:
                print(f"  Content: {response.text[:100]}...")
            else:
                print(f"  Content: EMPTY")
                
    except Exception as e:
        print(f"  Error: {e}")

async def main():
    """Run debug tests"""
    await debug_api()
    await test_alternative_formats()

if __name__ == "__main__":
    asyncio.run(main()) 