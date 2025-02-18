"""Tests for the Filter Agent."""

import pytest
from datetime import datetime, timedelta
from agents.scraper_agent import Grant
from agents.filter_agent import FilterAgent, GrantScore

@pytest.fixture
def mock_config():
    """Fixture providing test configuration."""
    return {
        'keywords': {
            'high_priority': ['blockchain', 'web3', 'crypto'],
            'medium_priority': ['defi', 'nft', 'dao'],
            'low_priority': ['technology', 'software', 'development']
        },
        'focus_areas': ['blockchain', 'defi', 'web3'],
        'user_profile': {
            'organization_type': 'startup',
            'mission_statement': 'Building decentralized finance solutions',
            'previous_grants': [
                {'amount': 50000},
                {'amount': 75000}
            ]
        },
        'min_grant_amount': 10000,
        'target_grant_amount': 100000,
        'min_days_to_deadline': 7,
        'max_days_to_deadline': 90,
        'high_effort_amount_threshold': 100000,
        'min_score_threshold': 0.5
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

def test_filter_agent_initialization(mock_config):
    """Test that the filter agent initializes correctly."""
    agent = FilterAgent(mock_config)
    assert agent.config == mock_config
    assert agent.logger is not None
    assert len(agent.keywords['high_priority']) == 3
    assert len(agent.focus_areas) == 3

def test_preprocess_text():
    """Test text preprocessing."""
    agent = FilterAgent({})
    text = "Web3 & Blockchain-based DeFi!!"
    processed = agent._preprocess_text(text)
    assert processed == "web3 blockchain based defi"

def test_extract_keywords():
    """Test keyword extraction."""
    agent = FilterAgent({})
    text = "Web3 & Blockchain-based DeFi!!"
    keywords = agent._extract_keywords(text)
    assert keywords == {'web3', 'blockchain', 'based', 'defi'}

def test_keyword_match_score(mock_config):
    """Test keyword matching score calculation."""
    agent = FilterAgent(mock_config)
    
    # Test with all high priority keywords
    keywords = {'blockchain', 'web3', 'crypto'}
    score = agent._calculate_keyword_match_score(keywords)
    assert 0 <= score <= 1
    
    # Calculate expected score for all high priority matches
    total_weights = (
        len(agent.keywords['high_priority']) * 2.0 +  # High priority weight
        len(agent.keywords['medium_priority']) * 0.6 +  # Medium priority weight
        len(agent.keywords['low_priority']) * 0.3  # Low priority weight
    )
    expected_score = (len(keywords) * 2.0) / total_weights  # All high priority matches
    assert abs(score - expected_score) < 0.001  # Allow for floating point imprecision

    # Test with mixed priority keywords
    keywords = {'blockchain', 'defi', 'technology'}  # 1 high, 1 medium, 1 low
    score = agent._calculate_keyword_match_score(keywords)
    assert 0 <= score <= 1
    
    # Calculate expected score for mixed priority matches
    expected_score = (1 * 2.0 + 1 * 0.6 + 1 * 0.3) / total_weights
    assert abs(score - expected_score) < 0.001  # Allow for floating point imprecision

def test_focus_match_score(mock_config):
    """Test focus area matching score calculation."""
    agent = FilterAgent(mock_config)
    keywords = {'blockchain', 'defi', 'other'}  # 2 matches out of 3 focus areas
    score = agent._calculate_focus_match_score(keywords)
    assert score == 2/3

def test_org_match_score(mock_config, sample_grant):
    """Test organization matching score calculation."""
    agent = FilterAgent(mock_config)
    score = agent._calculate_org_match_score(sample_grant)
    assert 0 <= score <= 1
    assert score > 0.5  # Should be high due to matching org type and amount range

def test_relevance_score(mock_config, sample_grant):
    """Test overall relevance score calculation."""
    agent = FilterAgent(mock_config)
    score = agent.calculate_relevance_score(sample_grant)
    assert 0 <= score <= 1
    assert score > 0.5  # Should be high due to matching keywords and profile

def test_amount_score(mock_config, sample_grant):
    """Test amount score calculation."""
    agent = FilterAgent(mock_config)
    
    # Create a copy of the grant to modify
    grant = Grant(
        id=sample_grant.id,
        title=sample_grant.title,
        description=sample_grant.description,
        amount=sample_grant.amount,
        deadline=sample_grant.deadline,
        source=sample_grant.source,
        url=sample_grant.url,
        eligibility=sample_grant.eligibility
    )
    
    # Test below minimum
    grant.amount = 5000
    assert agent.calculate_amount_score(grant) == 0.0
    
    # Test at target
    grant.amount = 100000
    assert agent.calculate_amount_score(grant) == 1.0
    
    # Test in between
    grant.amount = 55000
    score = agent.calculate_amount_score(grant)
    assert 0 < score < 1

def test_urgency_score(mock_config, sample_grant):
    """Test urgency score calculation."""
    agent = FilterAgent(mock_config)
    
    # Create a copy of the grant to modify
    grant = Grant(
        id=sample_grant.id,
        title=sample_grant.title,
        description=sample_grant.description,
        amount=sample_grant.amount,
        deadline=sample_grant.deadline,
        source=sample_grant.source,
        url=sample_grant.url,
        eligibility=sample_grant.eligibility
    )
    
    # Test too urgent
    grant.deadline = datetime.now() + timedelta(days=5)
    assert agent.calculate_urgency_score(grant) == 0.0
    
    # Test too far
    grant.deadline = datetime.now() + timedelta(days=100)
    assert agent.calculate_urgency_score(grant) == 0.2
    
    # Test optimal range
    grant.deadline = datetime.now() + timedelta(days=30)
    score = agent.calculate_urgency_score(grant)
    assert 0 < score < 1

def test_effort_score(mock_config, sample_grant):
    """Test effort score calculation."""
    agent = FilterAgent(mock_config)
    
    # Create a copy of the grant to modify
    grant = Grant(
        id=sample_grant.id,
        title=sample_grant.title,
        description=sample_grant.description,
        amount=sample_grant.amount,
        deadline=sample_grant.deadline,
        source=sample_grant.source,
        url=sample_grant.url,
        eligibility=sample_grant.eligibility
    )
    
    # Test high effort indicators
    grant.description = "Detailed comprehensive project requiring partnerships and multiple phases"
    score1 = agent.calculate_effort_score(grant)
    
    # Test low effort indicators
    grant.description = "Simple and straightforward project with basic requirements"
    score2 = agent.calculate_effort_score(grant)
    
    assert score1 < score2  # High effort should have lower score

def test_score_grant(mock_config, sample_grant):
    """Test comprehensive grant scoring."""
    agent = FilterAgent(mock_config)
    score = agent.score_grant(sample_grant)
    
    assert isinstance(score, GrantScore)
    assert 0 <= score.total_score <= 1
    assert 0 <= score.relevance_score <= 1
    assert 0 <= score.amount_score <= 1
    assert 0 <= score.urgency_score <= 1
    assert 0 <= score.effort_score <= 1

def test_filter_grants(mock_config):
    """Test grant filtering and sorting."""
    agent = FilterAgent(mock_config)
    
    # Create grants with different characteristics
    grants = [
        Grant(
            id="high-score",
            title="Web3 Development",
            description="Blockchain project with good fit",
            amount=50000.0,
            deadline=datetime.now() + timedelta(days=30),
            source="test",
            url="https://test.com/1",
            eligibility="Open to startups"
        ),
        Grant(
            id="low-score",
            title="Art Project",
            description="Unrelated to focus areas",
            amount=5000.0,
            deadline=datetime.now() + timedelta(days=5),
            source="test",
            url="https://test.com/2",
            eligibility="Open to all"
        )
    ]
    
    scored_grants = agent.filter_grants(grants)
    
    assert len(scored_grants) >= 1  # At least high-score grant should pass
    assert scored_grants[0].grant.id == "high-score"  # Should be first 