#!/usr/bin/env python3
"""
Quick test script for CheckbookNYC adapter
Run this directly in Python without terminal dependencies
"""

import os
import sys
import asyncio

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("🔍 CheckbookNYC Integration Status Check")
print("=" * 50)

try:
    print("✅ Python path configured")
    print(f"   Current directory: {current_dir}")
    
    # Test importing the module
    from app.adapters.checkbook import search
    print("✅ Successfully imported checkbook adapter")
    
    # Test a simple search
    async def test_search():
        print("\n🧪 Testing CheckbookNYC API with 'Apple' query...")
        try:
            results = await search("Apple", 2024)
            print(f"✅ API call completed - {len(results)} results returned")
            
            if results:
                # Show dataset breakdown
                datasets = {}
                for r in results:
                    record_type = r.get('record_type', 'unknown')
                    datasets[record_type] = datasets.get(record_type, 0) + 1
                
                print("\n📊 Dataset Results:")
                for dataset, count in datasets.items():
                    print(f"   - {dataset.upper()}: {count} records")
                
                print(f"\n🏆 Top 3 Results:")
                for i, r in enumerate(results[:3]):
                    print(f"   {i+1}. {r['entity_name']} - {r['amount']} ({r['record_type']})")
            else:
                print("⚠️  No results returned (API may need authentication or different endpoints)")
                
        except Exception as e:
            print(f"❌ Error during API test: {e}")
            import traceback
            traceback.print_exc()
    
    # Run the async test
    asyncio.run(test_search())
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\n🔧 Troubleshooting:")
    print("   1. Make sure you're in the backend directory")
    print("   2. Check that app/adapters/checkbook.py exists")
    print("   3. Verify your Python environment is activated")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("🎯 Test Complete") 