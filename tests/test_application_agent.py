"""Tests for the Application Agent."""

import pytest
from datetime import datetime, timedelta
import json
import os
from unittest.mock import patch, MagicMock
from agents.scraper_agent import Grant
from agents.filter_agent import GrantScore
from agents.application_agent import ApplicationAgent, Application, ApplicationSection

@pytest.fixture
def mock_config():
    """Fixture providing test configuration."""
    return {
        'openai_model': 'gpt-4',
        'openai_api_key': 'test_key',
        'application_threshold': 0.7,
        'section_word_limits': {
            'Executive Summary': 300,
            'Project Description': 1000,
            'Methodology': 800,
            'Budget Narrative': 500
        },
        'user_profile': {
            'organization_name': 'Web3 Innovations',
            'organization_type': 'startup',
            'mission_statement': 'Building decentralized solutions',
            'core_competencies': [
                'Blockchain Development',
                'Smart Contract Engineering'
            ],
            'team_size': 12,
            'previous_grants': [
                {'name': 'ETH Grant', 'amount': 50000, 'year': 2023}
            ]
        },
        'storage': {
            'applications_dir': 'data/test_applications'
        }
    }

@pytest.fixture
def sample_grant():
    """Fixture providing a sample grant for testing."""
    return Grant(
        id="test-grant-1",
        title="Web3 Development Grant",
        description="A grant for blockchain and web3 development projects",
        amount=50000.0,
        deadline=datetime.now() + timedelta(days=30),
        source="test_source",
        url="https://test.grants.com/grants/1",
        eligibility="Open to startups and small organizations"
    )

@pytest.fixture
def sample_grant_score(sample_grant):
    """Fixture providing a sample scored grant."""
    return GrantScore(
        grant=sample_grant,
        relevance_score=0.8,
        amount_score=0.7,
        urgency_score=0.6,
        effort_score=0.9,
        total_score=0.75,
        notes=None
    )

@pytest.fixture
def mock_openai_response():
    """Fixture providing a mock OpenAI API response."""
    class MockResponse:
        def __init__(self, content):
            self.choices = [MagicMock(message=MagicMock(content=content))]
    
    return MockResponse("Generated test content for the application section.")

def test_application_agent_initialization(mock_config):
    """Test that the application agent initializes correctly."""
    agent = ApplicationAgent(mock_config)
    assert agent.config == mock_config
    assert agent.logger is not None
    assert len(agent.section_templates) > 0

def test_load_template():
    """Test template loading functionality."""
    agent = ApplicationAgent({})
    template = agent._load_template("executive_summary")
    assert template != ""
    assert "{grant_title}" in template
    assert "{grant_description}" in template

def test_format_prompt_variables(mock_config, sample_grant):
    """Test prompt variable formatting."""
    agent = ApplicationAgent(mock_config)
    template = agent.section_templates["Executive Summary"]
    formatted = agent._format_prompt_variables(template, sample_grant, "Executive Summary")
    
    assert sample_grant.title in formatted
    assert sample_grant.description in formatted
    assert mock_config['user_profile']['organization_name'] in formatted

@patch('openai.ChatCompletion.acreate')
async def test_generate_section_content(mock_acreate, mock_config, sample_grant, mock_openai_response):
    """Test section content generation."""
    mock_acreate.return_value = mock_openai_response
    
    agent = ApplicationAgent(mock_config)
    content = await agent.generate_section_content(
        "Executive Summary",
        sample_grant,
        max_words=300
    )
    
    assert content == mock_openai_response.choices[0].message.content
    assert mock_acreate.called
    call_args = mock_acreate.call_args[1]
    assert call_args['model'] == 'gpt-4'
    assert len(call_args['messages']) == 2

@patch('openai.ChatCompletion.acreate')
async def test_generate_application(mock_acreate, mock_config, sample_grant, mock_openai_response, tmp_path):
    """Test complete application generation."""
    mock_acreate.return_value = mock_openai_response
    
    # Modify config to use temporary directory
    test_config = mock_config.copy()
    test_config['storage'] = {'applications_dir': str(tmp_path)}
    
    agent = ApplicationAgent(test_config)
    application = await agent.generate_application(sample_grant)
    
    assert isinstance(application, Application)
    assert len(application.sections) > 0
    assert all(isinstance(s, ApplicationSection) for s in application.sections)
    assert application.status == "in_progress"
    
    # Check that files were created
    app_dir = os.path.join(tmp_path, f"{sample_grant.source}_{sample_grant.id}")
    assert os.path.exists(app_dir)
    assert os.path.exists(os.path.join(app_dir, 'metadata.json'))
    assert any(f.endswith('.md') for f in os.listdir(app_dir))

@patch('openai.ChatCompletion.acreate')
async def test_save_application(mock_acreate, mock_config, sample_grant, mock_openai_response, tmp_path):
    """Test application saving functionality."""
    mock_acreate.return_value = mock_openai_response
    
    # Modify config to use temporary directory
    test_config = mock_config.copy()
    test_config['storage'] = {'applications_dir': str(tmp_path)}
    
    agent = ApplicationAgent(test_config)
    application = await agent.generate_application(sample_grant)
    
    # Check metadata file
    metadata_path = os.path.join(
        tmp_path,
        f"{sample_grant.source}_{sample_grant.id}",
        'metadata.json'
    )
    assert os.path.exists(metadata_path)
    
    with open(metadata_path) as f:
        metadata = json.load(f)
        assert metadata['grant_id'] == sample_grant.id
        assert metadata['status'] == "in_progress"

@patch('openai.ChatCompletion.acreate')
async def test_process_grants(
    mock_acreate,
    mock_config,
    sample_grant_score,
    mock_openai_response,
    tmp_path
):
    """Test processing multiple grants."""
    mock_acreate.return_value = mock_openai_response
    
    # Modify config to use temporary directory
    test_config = mock_config.copy()
    test_config['storage'] = {'applications_dir': str(tmp_path)}
    
    agent = ApplicationAgent(test_config)
    applications = await agent.process_grants([sample_grant_score])
    
    assert len(applications) == 1
    assert isinstance(applications[0], Application)
    assert len(applications[0].sections) > 0

@patch('openai.ChatCompletion.acreate')
async def test_word_limit_enforcement(mock_acreate, mock_config, sample_grant):
    """Test that word limits are enforced."""
    # Create a response that exceeds word limit
    long_response = "Generated content. " * 200  # Way more than 300 words
    mock_acreate.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=long_response))]
    )
    
    agent = ApplicationAgent(mock_config)
    content = await agent.generate_section_content(
        "Executive Summary",
        sample_grant,
        max_words=300
    )
    
    # Check that content was truncated
    assert len(content.split()) <= 300
    assert content.endswith('...')

@patch('openai.ChatCompletion.acreate')
async def test_error_handling(mock_acreate, mock_config, sample_grant_score):
    """Test error handling during application generation."""
    # Simulate API error
    mock_acreate.side_effect = Exception("API Error")
    
    agent = ApplicationAgent(mock_config)
    applications = await agent.process_grants([sample_grant_score])
    
    # Should handle error gracefully and return empty list
    assert len(applications) == 0 