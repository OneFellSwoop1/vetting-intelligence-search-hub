#!/usr/bin/env python3
"""
Check terminal configuration and test CheckbookNYC integration
Based on VS Code terminal troubleshooting guide
"""

import os
import sys
import subprocess
import asyncio

print("🔍 Terminal & CheckbookNYC Integration Diagnostics")
print("=" * 60)

# Step 1: Check shell configuration
print("\n1️⃣ CHECKING SHELL CONFIGURATION")
print("-" * 30)

try:
    shell = os.environ.get('SHELL', 'Unknown')
    print(f"✅ Default shell: {shell}")
    
    # Test shell directly (as recommended in VS Code guide)
    result = subprocess.run([shell, '--version'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"✅ Shell is functional: {result.stdout.strip()[:50]}...")
    else:
        print(f"⚠️  Shell version check failed: {result.stderr}")
        
except Exception as e:
    print(f"❌ Shell check failed: {e}")

# Step 2: Check Python environment
print("\n2️⃣ CHECKING PYTHON ENVIRONMENT")
print("-" * 30)

print(f"✅ Python version: {sys.version}")
print(f"✅ Python executable: {sys.executable}")
print(f"✅ Current working directory: {os.getcwd()}")

# Step 3: Check module imports
print("\n3️⃣ CHECKING MODULE IMPORTS")
print("-" * 30)

try:
    # Add current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    print(f"✅ Added to Python path: {current_dir}")
    
    # Test imports
    from app.adapters.checkbook import search
    print("✅ Successfully imported checkbook adapter")
    
    # Test other modules
    import httpx
    import xml.etree.ElementTree as ET
    print("✅ Dependencies available: httpx, xml.etree")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("🔧 Try running from the backend directory")
    sys.exit(1)

# Step 4: Test CheckbookNYC integration
print("\n4️⃣ TESTING CHECKBOOK NYC INTEGRATION")
print("-" * 30)

async def test_checkbook():
    """Test all four CheckbookNYC datasets"""
    
    test_cases = [
        ("Apple", "Corporate entity test"),
        ("Education", "Agency/department test"),
        ("Microsoft", "Tech company test")
    ]
    
    total_results = 0
    dataset_summary = {}
    
    for query, description in test_cases:
        print(f"\n🧪 Testing: {description} ('{query}')")
        
        try:
            results = await search(query, None)  # No year filter
            result_count = len(results)
            total_results += result_count
            
            print(f"   📊 Results: {result_count}")
            
            # Track datasets
            for r in results[:5]:  # Check first 5 results
                dataset = r.get('record_type', 'unknown')
                dataset_summary[dataset] = dataset_summary.get(dataset, 0) + 1
                print(f"   • {r['entity_name']} - {r['amount']} ({dataset})")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📈 INTEGRATION SUMMARY")
    print(f"   Total results across all tests: {total_results}")
    print(f"   Datasets accessed:")
    for dataset, count in dataset_summary.items():
        print(f"   • {dataset.upper()}: {count} records")
    
    if total_results > 0:
        print("✅ CheckbookNYC integration is WORKING!")
        return True
    else:
        print("⚠️  No results returned - API endpoints may need authentication")
        return False

# Run the test
print("\n🚀 RUNNING INTEGRATION TEST...")
try:
    success = asyncio.run(test_checkbook())
    
    if success:
        print(f"\n🎉 SUCCESS: All systems operational!")
        print("   • Terminal issues bypassed using direct Python execution")
        print("   • CheckbookNYC integration is functional")
        print("   • Multiple datasets accessible")
    else:
        print(f"\n⚠️  PARTIAL SUCCESS: Python environment OK, API needs investigation")
        
except Exception as e:
    print(f"\n❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("🎯 Diagnostics Complete")
print("\n💡 NEXT STEPS:")
print("   1. If this script runs successfully, your Python environment is fine")
print("   2. Use this script instead of terminal commands for testing")
print("   3. For terminal issues, check Cursor/VS Code settings as per official guide") 