#!/usr/bin/env python3
"""
Test to see full error message from NYC Checkbook API
"""

import asyncio
import httpx
import xmltodict

APP_TOKEN = "2UYrUskVvUcZM1VR5e06dvfV"
API_URL = "https://www.checkbooknyc.com/api"

# Test without XML declaration (this got a response)
xml_body = """<request>
  <type_of_data>Contracts</type_of_data>
  <records_from>1</records_from>
  <max_records>5</max_records>
</request>"""

async def test_full_response():
    headers = {
        'Content-Type': 'application/xml',
        'X-App-Token': APP_TOKEN,
        'User-Agent': 'Vetting-Intelligence-Debug/1.0'
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(API_URL, headers=headers, content=xml_body)
        
        print("🔍 FULL API RESPONSE")
        print("=" * 50)
        print(f"Status: {response.status_code}")
        print(f"Response Body:")
        print(response.text)
        print()
        
        if response.text:
            try:
                parsed = xmltodict.parse(response.text)
                print("📊 Parsed XML:")
                import json
                print(json.dumps(parsed, indent=2))
            except Exception as e:
                print(f"XML parsing error: {e}")

asyncio.run(test_full_response()) 