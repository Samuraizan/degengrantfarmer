#!/usr/bin/env python3
"""
Degen Grant Farmer - Main Script

This script orchestrates the grant farming process by coordinating the three main agents:
1. Scraper Agent - Collects grant opportunities
2. Filter Agent - Ranks and selects promising grants
3. Application Agent - Generates applications for selected grants
"""

import asyncio
import logging
import os
import yaml
from datetime import datetime
from typing import Dict, List

from agents.scraper_agent import ScraperAgent, Grant
from agents.filter_agent import FilterAgent
from agents.application_agent import ApplicationAgent

def setup_logging(config: Dict) -> None:
    """Set up logging configuration."""
    log_config = config.get('logging', {})
    
    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_config.get('file', 'data/logs/dgf.log')), exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_config.get('file', 'data/logs/dgf.log')),
            logging.StreamHandler()
        ]
    )

def load_config() -> Dict:
    """Load configuration from YAML file."""
    config_path = os.path.join('config', 'settings.yaml')
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Load API keys from environment
    config['openai_api_key'] = os.getenv('OPENAI_API_KEY')
    
    return config

async def main():
    """Main execution function."""
    # Load configuration
    config = load_config()
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Degen Grant Farmer")
    
    try:
        # Initialize agents
        scraper = ScraperAgent(config.get('scraper', {}))
        filter_agent = FilterAgent(config.get('filter', {}))
        application_agent = ApplicationAgent(config.get('application', {}))
        
        # Run scraper to collect grants
        logger.info("Starting grant collection")
        grants = scraper.run()
        logger.info(f"Collected {len(grants)} grants")
        
        if not grants:
            logger.warning("No grants found, ending run")
            return
        
        # Filter and score grants
        logger.info("Filtering and scoring grants")
        scored_grants = filter_agent.filter_grants(grants)
        logger.info(f"Found {len(scored_grants)} promising grants")
        
        if not scored_grants:
            logger.warning("No grants passed filtering, ending run")
            return
        
        # Generate applications for top grants
        logger.info("Generating applications")
        applications = await application_agent.process_grants(scored_grants)
        logger.info(f"Generated {len(applications)} applications")
        
        # Save results
        storage_config = config.get('storage', {})
        os.makedirs(os.path.dirname(storage_config.get('grants_file', 'data/raw/grants.json')), exist_ok=True)
        os.makedirs(os.path.dirname(storage_config.get('filtered_grants_file', 'data/processed/filtered_grants.json')), exist_ok=True)
        os.makedirs(storage_config.get('applications_dir', 'data/applications/'), exist_ok=True)
        
        # TODO: Implement proper serialization of results
        logger.info("Run completed successfully")
        
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main()) 