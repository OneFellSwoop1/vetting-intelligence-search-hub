#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from environment.env file"""
    env_file = Path(__file__).parent / 'environment.env'
    
    if env_file.exists():
        print(f"📄 Loading environment from: {env_file}")
        
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                    print(f"   ✅ Loaded: {key}")
        
        return True
    else:
        print(f"❌ Environment file not found: {env_file}")
        return False

async def test_with_credentials():
    """Test Checkbook adapter with properly loaded credentials"""
    
    print('🔐 ENVIRONMENT CREDENTIAL TEST')
    print('=' * 50)
    
    # Step 1: Load environment file
    env_loaded = load_env_file()
    
    if not env_loaded:
        print("❌ Cannot proceed without environment file")
        return
    
    # Step 2: Verify credentials are loaded
    api_key_id = os.getenv('SOCRATA_API_KEY_ID')
    api_key_secret = os.getenv('SOCRATA_API_KEY_SECRET')
    app_token = os.getenv('SOCRATA_APP_TOKEN')
    
    print(f"\n🔍 Environment Variable Check:")
    print(f"   - SOCRATA_API_KEY_ID: {'✅ Loaded' if api_key_id else '❌ Missing'}")
    print(f"   - SOCRATA_API_KEY_SECRET: {'✅ Loaded' if api_key_secret else '❌ Missing'}")
    print(f"   - SOCRATA_APP_TOKEN: {'✅ Loaded' if app_token else '❌ Missing'}")
    
    if api_key_id:
        print(f"   - API Key ID (first 10 chars): {api_key_id[:10]}...")
    if app_token:
        print(f"   - App Token (first 10 chars): {app_token[:10]}...")
    
    # Step 3: Test adapter with credentials
    try:
        sys.path.append('.')
        from app.adapters.checkbook import CheckbookNYCAdapter
        
        adapter = CheckbookNYCAdapter()
        
        print(f"\n🧪 Testing CheckbookNYC with authenticated access...")
        results = await adapter.search('Microsoft', 2024)
        
        if results:
            print(f"✅ SUCCESS: {len(results)} results with authentication")
            
            # Test data quality
            amounts = [r.get('amount', 0) for r in results if r.get('amount', 0) > 0]
            total_amount = sum(amounts)
            
            print(f"   - Total contract value: ${total_amount:,.2f}")
            print(f"   - Valid records with amounts: {len(amounts)}/{len(results)}")
            
            # Show top 3 results
            print(f"\n🏆 Top 3 Results:")
            for i, result in enumerate(results[:3]):
                vendor = result.get('vendor', 'Unknown')
                amount = result.get('amount', 0)
                agency = result.get('agency', 'Unknown')
                print(f"   {i+1}. {vendor} - ${amount:,.2f} ({agency})")
                
        else:
            print("⚠️  No results returned (may need different datasets)")
            
    except Exception as e:
        print(f"❌ Error testing adapter: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_with_credentials()) 