"""
Scraper Agent for Degen Grant Farmer.

This module implements the Scraper Agent responsible for collecting grant information
from various sources including web pages and APIs.
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime
import json
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel
import time
import os

class Grant(BaseModel):
    """Data model for a grant opportunity."""
    id: str
    title: str
    description: str
    amount: Optional[float]
    deadline: Optional[datetime]
    source: str
    url: str
    eligibility: Optional[str]
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class ScraperAgent:
    """Agent responsible for collecting grant information from various sources."""
    
    def __init__(self, config: Dict):
        """Initialize the scraper agent with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        
    def _scrape_grants_gov(self, source: Dict) -> List[Grant]:
        """
        Scrape grants from Grants.gov API.
        
        Args:
            source: Source configuration dictionary
            
        Returns:
            List of Grant objects
        """
        grants = []
        url = source['url']
        
        try:
            # Grants.gov API parameters
            params = {
                'keyword': '',  # Can be configured for specific searches
                'oppStatus': 'posted',
                'sortBy': 'openDate&sortOrder=desc',
                'rows': 10  # Limit for testing, can be increased
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            opportunities = data.get('opportunities', [])
            
            for opp in opportunities:
                try:
                    # Parse amount from award ceiling
                    amount = None
                    if 'awardCeiling' in opp:
                        try:
                            amount = float(opp['awardCeiling'])
                        except (ValueError, TypeError):
                            pass
                    
                    # Parse deadline
                    deadline = None
                    if 'closeDate' in opp:
                        try:
                            deadline = datetime.strptime(opp['closeDate'], '%Y-%m-%d')
                        except ValueError:
                            pass
                    
                    grant = Grant(
                        id=f"grants_gov_{opp.get('opportunityNumber', '')}",
                        title=opp.get('opportunityTitle', ''),
                        description=opp.get('description', ''),
                        amount=amount,
                        deadline=deadline,
                        source='grants_gov',
                        url=f"https://www.grants.gov/web/grants/view-opportunity.html?oppId={opp.get('opportunityId')}",
                        eligibility=opp.get('eligibility', '')
                    )
                    grants.append(grant)
                    
                except Exception as e:
                    self.logger.error(f"Error parsing grant {opp.get('opportunityNumber', 'unknown')}: {str(e)}")
                    continue
                    
            return grants
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching from Grants.gov: {str(e)}")
            return []
    
    def _scrape_gitcoin(self, source: Dict) -> List[Grant]:
        """
        Scrape grants from Gitcoin website.
        
        Args:
            source: Source configuration dictionary
            
        Returns:
            List of Grant objects
        """
        grants = []
        url = source['url']
        
        try:
            # Add headers to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find grant listings (this will need to be updated based on Gitcoin's HTML structure)
            grant_elements = soup.find_all('div', class_='grant-card')  # Adjust class name as needed
            
            for element in grant_elements:
                try:
                    # Extract grant details (adjust selectors based on actual HTML)
                    title_elem = element.find('h3', class_='grant-title')
                    desc_elem = element.find('div', class_='grant-description')
                    amount_elem = element.find('span', class_='grant-amount')
                    deadline_elem = element.find('span', class_='grant-deadline')
                    
                    # Parse amount if present
                    amount = None
                    if amount_elem:
                        amount_text = amount_elem.text.strip()
                        try:
                            # Remove currency symbol and convert to float
                            amount = float(amount_text.replace('$', '').replace(',', ''))
                        except ValueError:
                            pass
                    
                    # Parse deadline if present
                    deadline = None
                    if deadline_elem:
                        try:
                            deadline = datetime.strptime(deadline_elem.text.strip(), '%Y-%m-%d')
                        except ValueError:
                            pass
                    
                    grant = Grant(
                        id=f"gitcoin_{element.get('id', '')}",
                        title=title_elem.text.strip() if title_elem else '',
                        description=desc_elem.text.strip() if desc_elem else '',
                        amount=amount,
                        deadline=deadline,
                        source='gitcoin',
                        url=element.find('a')['href'] if element.find('a') else '',
                        eligibility=None  # Gitcoin typically doesn't have strict eligibility
                    )
                    grants.append(grant)
                    
                except Exception as e:
                    self.logger.error(f"Error parsing Gitcoin grant: {str(e)}")
                    continue
            
            return grants
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching from Gitcoin: {str(e)}")
            return []
    
    def scrape_source(self, source_id: str) -> List[Grant]:
        """
        Scrape a specific source for grant opportunities.
        
        Args:
            source_id: Identifier for the source to scrape
            
        Returns:
            List of Grant objects found from the source
        """
        self.logger.info(f"Starting scrape for source: {source_id}")
        
        # Find source config
        source = next(
            (s for s in self.config.get('sources', []) if s['id'] == source_id),
            None
        )
        
        if not source:
            self.logger.error(f"Source configuration not found for {source_id}")
            return []
        
        # Add delay between requests to be polite
        time.sleep(1)
        
        # Route to appropriate scraper based on source type
        if source_id == 'grants_gov':
            return self._scrape_grants_gov(source)
        elif source_id == 'gitcoin':
            return self._scrape_gitcoin(source)
        else:
            self.logger.warning(f"Unknown source type: {source_id}")
            return []
    
    def run(self) -> List[Grant]:
        """
        Run a complete scraping cycle across all configured sources.
        
        Returns:
            Combined list of all grants found
        """
        all_grants = []
        for source in self.config.get('sources', []):
            try:
                grants = self.scrape_source(source['id'])
                self.logger.info(f"Found {len(grants)} grants from {source['id']}")
                all_grants.extend(grants)
            except Exception as e:
                self.logger.error(f"Error scraping source {source['id']}: {str(e)}")
                continue
        
        # Save raw grants to file
        if all_grants:
            storage_path = self.config.get('storage', {}).get('grants_file', 'data/raw/grants.json')
            os.makedirs(os.path.dirname(storage_path), exist_ok=True)
            
            try:
                with open(storage_path, 'w') as f:
                    # Convert grants to dict for JSON serialization using model_dump
                    grants_data = [grant.model_dump() for grant in all_grants]
                    json.dump(grants_data, f, indent=2, default=str)
            except Exception as e:
                self.logger.error(f"Error saving grants to file: {str(e)}")
        
        return all_grants 