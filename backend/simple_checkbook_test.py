#!/usr/bin/env python3
"""
Simple CheckbookNYC test that works regardless of terminal issues
Run this file directly in Cursor with Cmd+F5
"""

print("🚀 SIMPLE CHECKBOOK NYC TEST")
print("=" * 40)

# Test 1: Basic imports
print("1. Testing imports...")
try:
    import asyncio
    import sys
    import os
    print("✅ Standard libraries OK")
    
    # Add current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    from app.adapters.checkbook import search
    print("✅ CheckbookNYC adapter imported successfully")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    exit(1)

# Test 2: Quick API test
print("\n2. Testing CheckbookNYC API...")

async def quick_test():
    try:
        print("   Searching for 'Apple'...")
        results = await search("Apple", 2024)
        
        if results:
            print(f"✅ SUCCESS: {len(results)} results returned")
            
            # Show breakdown by dataset
            datasets = {}
            for r in results:
                dtype = r.get('record_type', 'unknown')
                datasets[dtype] = datasets.get(dtype, 0) + 1
            
            print("   📊 Dataset Results:")
            for dataset, count in datasets.items():
                print(f"      • {dataset}: {count} records")
            
            print("   🏆 Top 3 Results:")
            for i, r in enumerate(results[:3]):
                print(f"      {i+1}. {r['entity_name']} - {r['amount']}")
            
            return True
        else:
            print("⚠️  No results (API may need authentication)")
            return False
            
    except Exception as e:
        print(f"❌ API Error: {e}")
        return False

# Run the test
success = asyncio.run(quick_test())

print(f"\n{'='*40}")
if success:
    print("🎉 CHECKBOOK NYC INTEGRATION IS WORKING!")
    print("   • Multiple datasets accessible")
    print("   • No terminal dependencies needed")
else:
    print("⚠️  Integration needs investigation")
    print("   • Python environment is working")
    print("   • API endpoints may need authentication")

print("\n💡 To avoid terminal issues in the future:")
print("   • Use Cmd+F5 to run Python files directly")
print("   • Or right-click → 'Run Python File'")
print("   • This bypasses terminal launch problems") 