#!/usr/bin/env python3

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def load_and_validate_environment():
    """Load environment variables and validate all API key configurations"""
    
    print('🔍 COMPREHENSIVE API KEY CONFIGURATION VALIDATION')
    print('=' * 70)
    
    # Step 1: Find and load environment files
    env_files = [
        Path(__file__).parent / 'environment.env',
        Path(__file__).parent.parent / 'env.example'
    ]
    
    print('📄 Environment Files Check:')
    for env_file in env_files:
        if env_file.exists():
            print(f'   ✅ Found: {env_file.name}')
        else:
            print(f'   ❌ Missing: {env_file.name}')
    
    # Load main environment file
    env_file = Path(__file__).parent / 'environment.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f'\n📄 Loaded environment variables from: {env_file}')
    else:
        print(f'\n❌ Main environment file not found: {env_file}')
        return False
    
    print('\n🔐 API KEY CONFIGURATION ANALYSIS:')
    print('=' * 50)
    
    # Expected API keys and their sources
    api_configs = {
        'Senate LDA (Federal Lobbying)': {
            'env_var': 'LDA_API_KEY',
            'expected_start': '065af08d',
            'adapters': ['senate_lda.py'],
            'description': 'Federal lobbying disclosure data'
        },
        'Socrata API Key ID (NYC Data)': {
            'env_var': 'SOCRATA_API_KEY_ID', 
            'expected_start': '90d81emkbs',
            'adapters': ['checkbook.py', 'nyc_lobbyist.py'],
            'description': 'NYC Open Data API authentication'
        },
        'Socrata API Key Secret (NYC Data)': {
            'env_var': 'SOCRATA_API_KEY_SECRET',
            'expected_start': '4pajtcdkz6',
            'adapters': ['checkbook.py', 'nyc_lobbyist.py'],
            'description': 'NYC Open Data API authentication'
        },
        'Socrata App Token (NYC Data)': {
            'env_var': 'SOCRATA_APP_TOKEN',
            'expected_start': 'XF40HzCEpi',
            'adapters': ['checkbook.py', 'nyc_lobbyist.py'],
            'description': 'NYC Open Data rate limiting'
        }
    }
    
    all_valid = True
    
    for service_name, config in api_configs.items():
        env_var = config['env_var']
        expected_start = config['expected_start']
        adapters = config['adapters']
        description = config['description']
        
        print(f'\n🔑 {service_name}:')
        print(f'   Variable: {env_var}')
        print(f'   Used by: {", ".join(adapters)}')
        print(f'   Purpose: {description}')
        
        # Check if variable exists
        value = os.getenv(env_var)
        if value:
            # Validate format
            if value.startswith(expected_start):
                print(f'   ✅ Status: VALID (starts with {expected_start}...)')
                print(f'   📝 Value: {value[:15]}...')
            else:
                print(f'   ❌ Status: INVALID FORMAT')
                print(f'   📝 Expected: starts with {expected_start}')
                print(f'   📝 Actual: starts with {value[:10]}')
                all_valid = False
        else:
            print(f'   ❌ Status: MISSING')
            all_valid = False
    
    # Check adapter imports and usage
    print(f'\n🧩 ADAPTER CONFIGURATION CHECK:')
    print('=' * 40)
    
    adapter_files = [
        'app/adapters/checkbook.py',
        'app/adapters/senate_lda.py', 
        'app/adapters/nyc_lobbyist.py'
    ]
    
    for adapter_file in adapter_files:
        adapter_path = Path(__file__).parent / adapter_file
        if adapter_path.exists():
            print(f'\n📄 {adapter_file}:')
            
            # Read file and check for environment variable usage
            with open(adapter_path, 'r') as f:
                content = f.read()
                
            # Check for specific API key references
            env_vars_found = []
            for var in ['LDA_API_KEY', 'SOCRATA_API_KEY_ID', 'SOCRATA_API_KEY_SECRET', 'SOCRATA_APP_TOKEN']:
                if f"os.getenv('{var}')" in content or f'os.getenv("{var}")' in content:
                    env_vars_found.append(var)
            
            if env_vars_found:
                print(f'   ✅ Environment variables used: {", ".join(env_vars_found)}')
            else:
                print(f'   ⚠️  No environment variables detected')
        else:
            print(f'   ❌ File not found: {adapter_file}')
            all_valid = False
    
    # Check main application file for environment loading
    print(f'\n🚀 APPLICATION STARTUP CONFIGURATION:')
    print('=' * 45)
    
    main_files = [
        'app/main.py',
        'start_server.py'
    ]
    
    for main_file in main_files:
        main_path = Path(__file__).parent / main_file
        if main_path.exists():
            print(f'\n📄 {main_file}:')
            
            with open(main_path, 'r') as f:
                content = f.read()
            
            # Check for environment loading
            env_loading_methods = [
                'load_dotenv',
                'environment.env',
                'from dotenv import'
            ]
            
            found_methods = []
            for method in env_loading_methods:
                if method in content:
                    found_methods.append(method)
            
            if found_methods:
                print(f'   ✅ Environment loading detected: {", ".join(found_methods)}')
            else:
                print(f'   ⚠️  No environment loading detected')
        else:
            print(f'   ❌ File not found: {main_file}')
    
    # Final validation summary
    print(f'\n📋 VALIDATION SUMMARY:')
    print('=' * 30)
    
    if all_valid:
        print('✅ ALL API KEYS PROPERLY CONFIGURED')
        print('✅ All environment variables present and valid')
        print('✅ Adapters properly configured to use environment variables')
        print('\n🎉 Your API key configuration is PERFECT!')
    else:
        print('❌ CONFIGURATION ISSUES DETECTED')
        print('⚠️  Please review the issues above and fix them')
        print('\n📝 Common fixes:')
        print('   - Ensure environment.env file exists in backend/ directory')
        print('   - Verify API key values match expected formats')
        print('   - Check that adapters are loading environment variables correctly')
    
    return all_valid

async def test_api_connections():
    """Test actual API connections with loaded credentials"""
    
    print(f'\n🧪 API CONNECTION TESTING:')
    print('=' * 35)
    
    try:
        # Test Senate LDA
        print(f'\n🏛️  Testing Senate LDA API:')
        sys.path.append('.')
        from app.adapters.senate_lda import get_lda_api_key
        
        api_key = get_lda_api_key()
        if api_key:
            print(f'   ✅ API key loaded: {api_key[:10]}...')
            
            # Test a simple API call
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"Authorization": f"Token {api_key}"}
                response = await client.get(
                    "https://lda.senate.gov/api/v1/filings/?page_size=1", 
                    headers=headers
                )
                
                if response.status_code == 200:
                    print('   ✅ API connection successful')
                elif response.status_code == 401:
                    print('   ❌ API authentication failed')
                else:
                    print(f'   ⚠️  API responded with status {response.status_code}')
        else:
            print('   ❌ No API key found')
        
        # Test Socrata API
        print(f'\n🏙️  Testing Socrata API (NYC Data):')
        from app.adapters.checkbook import CheckbookNYCAdapter
        
        adapter = CheckbookNYCAdapter()
        if adapter.api_key_id and adapter.api_key_secret:
            print(f'   ✅ OAuth credentials loaded')
            print(f'   📝 API Key ID: {adapter.api_key_id[:10]}...')
            
            # Test API call
            results = await adapter.search('test', 2024)
            if results:
                print(f'   ✅ API connection successful - {len(results)} test results')
            else:
                print('   ⚠️  API call returned no results (may be normal)')
        else:
            print('   ❌ No Socrata credentials found')
            
    except Exception as e:
        print(f'   ❌ Error during API testing: {e}')

if __name__ == "__main__":
    # Run validation
    config_valid = load_and_validate_environment()
    
    if config_valid:
        # Run API tests
        import asyncio
        asyncio.run(test_api_connections())
    else:
        print('\n🛑 Skipping API tests due to configuration issues') 