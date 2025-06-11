#!/usr/bin/env python3
"""
Test NYC Checkbook XML API with parameters in search_criteria
"""

import asyncio
import httpx
import xmltodict
import json

APP_TOKEN = "2UYrUskVvUcZM1VR5e06dvfV"
API_URL = "https://www.checkbooknyc.com/api"

# Test with parameters in search_criteria
CRITERIA_XML = """<request>
  <type_of_data>Contracts</type_of_data>
  <records_from>1</records_from>
  <max_records>5</max_records>
  <search_criteria>
    <status>A</status>
    <category>contracts</category>
  </search_criteria>
</request>"""

# Alternative test - maybe different values
ALT_XML = """<request>
  <type_of_data>Contracts</type_of_data>
  <records_from>1</records_from>
  <max_records>5</max_records>
  <search_criteria>
    <status>Active</status>
    <category>contract</category>
  </search_criteria>
</request>"""

# Test minimal request
MINIMAL_XML = """<request>
  <type_of_data>Contracts</type_of_data>
  <records_from>1</records_from>
  <max_records>5</max_records>
</request>"""

async def test_format(name, xml_body):
    headers = {
        'Content-Type': 'application/xml',
        'X-App-Token': APP_TOKEN,
        'User-Agent': 'Vetting-Intelligence-Test/1.0'
    }
    
    print(f"\n🧪 Testing {name}")
    print("=" * 50)
    print("Request Body:")
    print(xml_body)
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(API_URL, headers=headers, content=xml_body)
        
        print(f"Response Status: {response.status_code}")
        
        if response.text:
            try:
                parsed = xmltodict.parse(response.text)
                
                # Check result
                if 'response' in parsed:
                    status = parsed['response'].get('status', {})
                    result = status.get('result', '')
                    
                    if result == 'success':
                        print("🎉 SUCCESS!")
                        data = parsed['response'].get('data', {})
                        if data:
                            print(f"📊 Data keys: {list(data.keys())}")
                    else:
                        print(f"❌ Result: {result}")
                        messages = status.get('messages', {})
                        if messages:
                            if isinstance(messages.get('message'), list):
                                for msg in messages['message']:
                                    print(f"  - {msg.get('description', 'Unknown')}")
                            else:
                                msg = messages.get('message', {})
                                print(f"  - {msg.get('description', 'Unknown')}")
                
            except Exception as e:
                print(f"❌ XML parsing error: {e}")
                print(f"Raw response: {response.text[:200]}...")
        else:
            print("⚠️  Empty response")

async def main():
    await test_format("Parameters in search_criteria", CRITERIA_XML)
    await test_format("Alternative values", ALT_XML)
    await test_format("Minimal request", MINIMAL_XML)

asyncio.run(main()) 