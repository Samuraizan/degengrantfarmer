"""Tests for the Scraper Agent."""

import pytest
from datetime import datetime, timedelta
import json
from unittest.mock import patch, MagicMock
from agents.scraper_agent import ScraperAgent, Grant

@pytest.fixture
def mock_config():
    """Fixture providing test configuration."""
    return {
        'sources': [
            {
                'id': 'grants_gov',
                'type': 'api',
                'url': 'https://www.grants.gov/grantsws/rest/opportunities/search/'
            },
            {
                'id': 'gitcoin',
                'type': 'web',
                'url': 'https://grants.gitcoin.co/'
            }
        ],
        'storage': {
            'grants_file': 'data/raw/grants.json'
        }
    }

@pytest.fixture
def sample_grant():
    """Fixture providing a sample grant for testing."""
    return Grant(
        id="test-grant-1",
        title="Test Grant",
        description="A grant for testing",
        amount=10000.0,
        deadline=datetime.now() + timedelta(days=30),
        source="test_source",
        url="https://test.grants.com/grants/1",
        eligibility="Open to all testers"
    )

@pytest.fixture
def mock_grants_gov_response():
    """Fixture providing a mock Grants.gov API response."""
    return {
        "opportunities": [
            {
                "opportunityNumber": "TEST-2024-001",
                "opportunityTitle": "Test Federal Grant",
                "opportunityId": "12345",
                "description": "A test grant from Grants.gov",
                "awardCeiling": "50000",
                "closeDate": "2024-12-31",
                "eligibility": "Open to all organizations"
            }
        ]
    }

@pytest.fixture
def mock_gitcoin_html():
    """Fixture providing mock Gitcoin HTML content."""
    return """
    <div class="grant-card" id="grant-123">
        <h3 class="grant-title">Test Gitcoin Grant</h3>
        <div class="grant-description">A test grant from Gitcoin</div>
        <span class="grant-amount">$25,000</span>
        <span class="grant-deadline">2024-12-31</span>
        <a href="https://grants.gitcoin.co/123">View Grant</a>
    </div>
    """

def test_scraper_agent_initialization(mock_config):
    """Test that the scraper agent initializes correctly."""
    agent = ScraperAgent(mock_config)
    assert agent.config == mock_config
    assert agent.logger is not None
    assert agent.session is not None

@patch('requests.Session')
def test_scrape_grants_gov(mock_session, mock_config, mock_grants_gov_response):
    """Test scraping from Grants.gov."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = mock_grants_gov_response
    mock_session.return_value.get.return_value = mock_response
    
    agent = ScraperAgent(mock_config)
    grants = agent._scrape_grants_gov(mock_config['sources'][0])
    
    assert len(grants) == 1
    grant = grants[0]
    assert grant.source == 'grants_gov'
    assert grant.id == 'grants_gov_TEST-2024-001'
    assert grant.amount == 50000.0
    assert grant.deadline.strftime('%Y-%m-%d') == '2024-12-31'

@patch('requests.Session')
def test_scrape_gitcoin(mock_session, mock_config, mock_gitcoin_html):
    """Test scraping from Gitcoin."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.text = mock_gitcoin_html
    mock_session.return_value.get.return_value = mock_response
    
    agent = ScraperAgent(mock_config)
    grants = agent._scrape_gitcoin(mock_config['sources'][1])
    
    assert len(grants) == 1
    grant = grants[0]
    assert grant.source == 'gitcoin'
    assert grant.title == 'Test Gitcoin Grant'
    assert grant.amount == 25000.0
    assert grant.deadline.strftime('%Y-%m-%d') == '2024-12-31'

@patch('requests.Session')
def test_scrape_source_not_found(mock_session, mock_config):
    """Test handling of unknown source."""
    agent = ScraperAgent(mock_config)
    grants = agent.scrape_source('unknown_source')
    assert len(grants) == 0

@patch('requests.Session')
def test_run_saves_grants(mock_session, mock_config, mock_grants_gov_response, tmp_path, monkeypatch):
    """Test that run() saves grants to file."""
    # Setup mock responses
    mock_response_gov = MagicMock()
    mock_response_gov.json.return_value = mock_grants_gov_response
    mock_session.return_value.get.return_value = mock_response_gov
    
    # Modify config to use temporary directory
    test_config = mock_config.copy()
    test_config['storage'] = {'grants_file': str(tmp_path / 'grants.json')}
    
    agent = ScraperAgent(test_config)
    grants = agent.run()
    
    assert len(grants) > 0
    assert (tmp_path / 'grants.json').exists()
    
    # Verify saved JSON
    with open(tmp_path / 'grants.json') as f:
        saved_data = json.load(f)
        assert len(saved_data) == len(grants)
        assert saved_data[0]['source'] == 'grants_gov'

def test_run_handles_source_error(mock_config):
    """Test that run() handles errors from individual sources gracefully."""
    agent = ScraperAgent(mock_config)
    results = agent.run()
    assert isinstance(results, list)
    # Even with an error, it should return an empty list not crash
    assert len(results) == 0

# TODO: Add more tests for actual scraping logic once implemented
# def test_scrape_source_with_mock_data():
#     pass 