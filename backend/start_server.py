#!/usr/bin/env python3

import os
import uvicorn
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Set environment variables
    os.environ['LDA_API_KEY'] = '065af08d580cf15c2220836fb456a5ebe504186c'
    
    logger.info("Starting Vetting Intelligence Search Hub backend...")
    logger.info(f"API Key set: {bool(os.environ.get('LDA_API_KEY'))}")
    
    try:
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise

if __name__ == "__main__":
    main() 