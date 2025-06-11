#!/usr/bin/env python3
"""
Test NYC Checkbook XML API with corrected format
"""

import asyncio
import httpx
import xmltodict
import json

APP_TOKEN = "2UYrUskVvUcZM1VR5e06dvfV"
API_URL = "https://www.checkbooknyc.com/api"

# Corrected XML templates (no XML declaration, includes status and category)
CORRECTED_XML = """<request>
  <type_of_data>Contracts</type_of_data>
  <records_from>1</records_from>
  <max_records>5</max_records>
  <status>A</status>
  <category>contracts</category>
</request>"""

async def test_corrected_format():
    headers = {
        'Content-Type': 'application/xml',
        'X-App-Token': APP_TOKEN,
        'User-Agent': 'Vetting-Intelligence-Test/1.0'
    }
    
    print("🧪 Testing CORRECTED XML Format")
    print("=" * 50)
    print("Request Body:")
    print(CORRECTED_XML)
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(API_URL, headers=headers, content=CORRECTED_XML)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body:")
        print(response.text)
        print()
        
        if response.text:
            try:
                parsed = xmltodict.parse(response.text)
                print("📊 Parsed Response:")
                print(json.dumps(parsed, indent=2))
                
                # Check if successful
                if 'response' in parsed:
                    status = parsed['response'].get('status', {})
                    result = status.get('result', '')
                    
                    if result == 'success':
                        print("\n🎉 SUCCESS! API is working!")
                        
                        # Look for data
                        data = parsed['response'].get('data', {})
                        if data:
                            print(f"📊 Data structure: {list(data.keys())}")
                    else:
                        print(f"\n❌ API returned: {result}")
                        messages = status.get('messages', {})
                        if messages:
                            print("Error messages:")
                            if isinstance(messages.get('message'), list):
                                for msg in messages['message']:
                                    print(f"  - {msg.get('description', 'Unknown error')}")
                            else:
                                msg = messages.get('message', {})
                                print(f"  - {msg.get('description', 'Unknown error')}")
                
            except Exception as e:
                print(f"XML parsing error: {e}")

asyncio.run(test_corrected_format()) 