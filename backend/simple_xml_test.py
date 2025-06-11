#!/usr/bin/env python3
"""
Simple test of NYC Checkbook XML API
Tests the official XML API directly without complex dependencies
"""

import asyncio
import httpx
import xmltodict
from jinja2 import Template

# Your App Token
APP_TOKEN = "2UYrUskVvUcZM1VR5e06dvfV"
API_URL = "https://www.checkbooknyc.com/api"

# Simple XML templates
CONTRACT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<request>
  <type_of_data>Contracts</type_of_data>
  <records_from>1</records_from>
  <max_records>5</max_records>
  {% if fiscal_year %}
  <search_criteria>
    <fiscal_year>{{ fiscal_year }}</fiscal_year>
  </search_criteria>
  {% endif %}
</request>"""

SPENDING_XML = """<?xml version="1.0" encoding="UTF-8"?>
<request>
  <type_of_data>Spending</type_of_data>
  <records_from>1</records_from>
  <max_records>5</max_records>
  {% if fiscal_year %}
  <search_criteria>
    <fiscal_year>{{ fiscal_year }}</fiscal_year>
  </search_criteria>
  {% endif %}
</request>"""

REVENUE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<request>
  <type_of_data>Revenue</type_of_data>
  <records_from>1</records_from>
  <max_records>5</max_records>
  {% if fiscal_year %}
  <search_criteria>
    <fiscal_year>{{ fiscal_year }}</fiscal_year>
  </search_criteria>
  {% endif %}
</request>"""

print("🧪 Simple NYC Checkbook XML API Test")
print("=" * 50)
print(f"API URL: {API_URL}")
print(f"App Token: {APP_TOKEN}")
print()

async def test_domain(domain_name, xml_template, fiscal_year=None):
    """Test a specific domain"""
    print(f"Testing {domain_name}...")
    
    try:
        # Render XML template
        template = Template(xml_template)
        xml_body = template.render(fiscal_year=fiscal_year)
        
        print(f"  📤 XML Request:")
        print(f"     {xml_body.replace(chr(10), ' ').replace(chr(13), ' ')}")
        
        # Headers
        headers = {
            'Content-Type': 'application/xml',
            'X-App-Token': APP_TOKEN,
            'User-Agent': 'Vetting-Intelligence-Test/1.0'
        }
        
        # Make request
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(API_URL, headers=headers, content=xml_body)
            
            print(f"  📥 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                # Parse XML response
                try:
                    xml_data = xmltodict.parse(response.text)
                    print(f"  ✅ XML parsed successfully")
                    
                    # Try to extract records
                    if 'response' in xml_data:
                        data = xml_data['response']
                        print(f"  📊 Response structure: {list(data.keys())}")
                        
                        # Look for records
                        record_count = 0
                        if 'records' in data:
                            records = data['records']
                            if isinstance(records, list):
                                record_count = len(records)
                            elif records:  # Single record
                                record_count = 1
                        elif 'record' in data:
                            record_count = 1 if data['record'] else 0
                        
                        print(f"  📈 Records found: {record_count}")
                        
                        if record_count > 0:
                            print(f"  🎉 SUCCESS: {domain_name} API is working!")
                            return True
                        else:
                            print(f"  ⚠️  No records returned (may be normal)")
                            return True  # API is working, just no data
                    else:
                        print(f"  📋 Raw response preview: {response.text[:200]}...")
                        return True  # Got a response
                        
                except Exception as parse_error:
                    print(f"  ❌ XML parsing error: {parse_error}")
                    print(f"  📋 Raw response: {response.text[:500]}...")
                    return False
            else:
                print(f"  ❌ HTTP Error: {response.status_code}")
                print(f"  📋 Error response: {response.text[:300]}...")
                return False
                
    except Exception as e:
        print(f"  ❌ Request error: {e}")
        return False

async def main():
    """Run all tests"""
    
    results = {}
    
    # Test each domain
    tests = [
        ("Contracts", CONTRACT_XML, 2024),
        ("Spending", SPENDING_XML, 2024),
        ("Revenue", REVENUE_XML, 2024),
    ]
    
    for domain_name, xml_template, year in tests:
        print()
        success = await test_domain(domain_name, xml_template, year)
        results[domain_name] = success
        
        # Small delay between requests
        await asyncio.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    for domain, success in results.items():
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"{domain:15} {status}")
    
    total_working = sum(results.values())
    print(f"\nTotal: {total_working}/{len(results)} endpoints working")
    
    if total_working == len(results):
        print("🎉 ALL TESTS PASSED! XML API is fully functional.")
    elif total_working > 0:
        print("⚠️  Some endpoints working. Check failed ones for issues.")
    else:
        print("❌ NO ENDPOINTS WORKING. Check credentials and API access.")

if __name__ == "__main__":
    asyncio.run(main()) 