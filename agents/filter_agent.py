"""
Filter Agent for Degen Grant Farmer.

This module implements the Filter Agent responsible for analyzing and ranking
grant opportunities based on configured criteria.
"""

from typing import Dict, List, Optional, Set
import logging
from datetime import datetime
import re
from collections import Counter
from pydantic import BaseModel
from .scraper_agent import Grant

class GrantScore(BaseModel):
    """Data model for a scored grant opportunity."""
    grant: Grant
    relevance_score: float
    amount_score: float
    urgency_score: float
    effort_score: float
    total_score: float
    notes: Optional[str]

class FilterAgent:
    """Agent responsible for filtering and ranking grant opportunities."""
    
    def __init__(self, config: Dict):
        """Initialize the filter agent with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize keyword sets from config
        self.keywords = {
            'high_priority': set(self.config.get('keywords', {}).get('high_priority', [])),
            'medium_priority': set(self.config.get('keywords', {}).get('medium_priority', [])),
            'low_priority': set(self.config.get('keywords', {}).get('low_priority', []))
        }
        
        # Initialize domain focus areas from config
        self.focus_areas = set(self.config.get('focus_areas', []))
        
        # Load organization profile for matching
        self.org_profile = self.config.get('user_profile', {})
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for keyword matching.
        
        Args:
            text: Input text to process
            
        Returns:
            Processed text (lowercase, cleaned)
        """
        # Convert to lowercase
        text = text.lower()
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        # Normalize whitespace
        text = ' '.join(text.split())
        return text
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """
        Extract keywords from text.
        
        Args:
            text: Input text to process
            
        Returns:
            Set of keywords found
        """
        words = set(self._preprocess_text(text).split())
        return words
    
    def _calculate_keyword_match_score(self, grant_keywords: Set[str]) -> float:
        """
        Calculate score based on keyword matches.
        
        Args:
            grant_keywords: Set of keywords from grant
            
        Returns:
            Score between 0 and 1
        """
        # Calculate matches for each priority level
        high_matches = len(grant_keywords & self.keywords['high_priority'])
        medium_matches = len(grant_keywords & self.keywords['medium_priority'])
        low_matches = len(grant_keywords & self.keywords['low_priority'])
        
        # Weight the matches with higher emphasis on high priority
        weighted_score = (
            high_matches * 2.0 +  # Double weight for high priority
            medium_matches * 0.6 +
            low_matches * 0.3
        )
        
        # Normalize score (assuming max possible matches would be all keywords)
        max_possible = (
            len(self.keywords['high_priority']) * 2.0 +  # Double weight for high priority
            len(self.keywords['medium_priority']) * 0.6 +
            len(self.keywords['low_priority']) * 0.3
        )
        
        return min(weighted_score / max_possible if max_possible > 0 else 0, 1.0)
    
    def _calculate_focus_match_score(self, grant_keywords: Set[str]) -> float:
        """
        Calculate how well grant matches focus areas.
        
        Args:
            grant_keywords: Set of keywords from grant
            
        Returns:
            Score between 0 and 1
        """
        if not self.focus_areas:
            return 0.5  # Neutral score if no focus areas defined
        
        matches = len(grant_keywords & self.focus_areas)
        return min(matches / len(self.focus_areas), 1.0)
    
    def _calculate_org_match_score(self, grant: Grant) -> float:
        """
        Calculate how well grant matches organization profile.
        
        Args:
            grant: Grant to evaluate
            
        Returns:
            Score between 0 and 1
        """
        matches = 0
        total_criteria = 0
        
        # Check organization type match
        if self.org_profile.get('organization_type') and grant.eligibility:
            total_criteria += 1
            if self.org_profile['organization_type'].lower() in grant.eligibility.lower():
                matches += 1
        
        # Check if grant amount is within org's typical range
        if grant.amount and self.org_profile.get('previous_grants'):
            total_criteria += 1
            avg_previous = sum(g.get('amount', 0) for g in self.org_profile['previous_grants']) / len(self.org_profile['previous_grants'])
            if 0.5 * avg_previous <= grant.amount <= 2 * avg_previous:
                matches += 1
        
        # Check mission alignment
        if self.org_profile.get('mission_statement') and grant.description:
            total_criteria += 1
            mission_keywords = self._extract_keywords(self.org_profile['mission_statement'])
            grant_keywords = self._extract_keywords(grant.description)
            if len(mission_keywords & grant_keywords) / len(mission_keywords) > 0.3:  # 30% overlap threshold
                matches += 1
        
        return matches / total_criteria if total_criteria > 0 else 0.5
        
    def calculate_relevance_score(self, grant: Grant) -> float:
        """Calculate how relevant a grant is to the user's profile/interests."""
        # Extract keywords from grant title and description
        grant_text = f"{grant.title} {grant.description}"
        grant_keywords = self._extract_keywords(grant_text)
        
        # Calculate component scores
        keyword_score = self._calculate_keyword_match_score(grant_keywords)
        focus_score = self._calculate_focus_match_score(grant_keywords)
        org_score = self._calculate_org_match_score(grant)
        
        # Weight the components (can be adjusted)
        weights = self.config.get('relevance_weights', {
            'keywords': 0.4,
            'focus': 0.3,
            'org_match': 0.3
        })
        
        total_score = (
            keyword_score * weights['keywords'] +
            focus_score * weights['focus'] +
            org_score * weights['org_match']
        )
        
        self.logger.debug(
            f"Relevance scores for {grant.id}: keywords={keyword_score:.2f}, "
            f"focus={focus_score:.2f}, org_match={org_score:.2f}, total={total_score:.2f}"
        )
        
        return total_score
        
    def calculate_amount_score(self, grant: Grant) -> float:
        """Calculate score based on grant amount/value."""
        if not grant.amount:
            return 0.5  # Neutral score if amount unknown
        
        min_amount = self.config.get('min_grant_amount', 0)
        target_amount = self.config.get('target_grant_amount', min_amount * 2)
        
        if grant.amount < min_amount:
            return 0.0
        elif grant.amount >= target_amount:
            return 1.0
        else:
            # Linear scaling between min and target
            return (grant.amount - min_amount) / (target_amount - min_amount)
    
    def calculate_urgency_score(self, grant: Grant) -> float:
        """Calculate score based on deadline urgency."""
        if not grant.deadline:
            return 0.5  # Neutral score if deadline unknown
            
        now = datetime.now()
        days_until_deadline = (grant.deadline - now).days
        
        min_days = self.config.get('min_days_to_deadline', 7)
        max_days = self.config.get('max_days_to_deadline', 90)
        
        if days_until_deadline < min_days:
            return 0.0  # Too urgent
        elif days_until_deadline > max_days:
            return 0.2  # Not urgent
        else:
            # Higher score for closer deadlines within acceptable range
            return 1.0 - ((days_until_deadline - min_days) / (max_days - min_days))
    
    def calculate_effort_score(self, grant: Grant) -> float:
        """Calculate score based on estimated application effort."""
        # Initialize base effort score
        base_score = 1.0
        
        # Analyze grant description and eligibility for complexity indicators
        text_to_analyze = f"{grant.description} {grant.eligibility or ''}"
        text_to_analyze = self._preprocess_text(text_to_analyze)
        
        # Complexity indicators (words that suggest more work)
        complexity_indicators = {
            'high_effort': [
                'detailed', 'comprehensive', 'extensive', 'multiple phases',
                'partnership', 'collaboration', 'match funding', 'audit',
                'reporting', 'milestone', 'deliverable'
            ],
            'medium_effort': [
                'proposal', 'budget', 'timeline', 'plan', 'team',
                'experience', 'qualification', 'documentation'
            ],
            'low_effort': [
                'simple', 'basic', 'straightforward', 'quick', 'easy'
            ]
        }
        
        # Count occurrences of complexity indicators
        for word in complexity_indicators['high_effort']:
            if word in text_to_analyze:
                base_score -= 0.15  # Higher penalty for high-effort indicators
        
        for word in complexity_indicators['medium_effort']:
            if word in text_to_analyze:
                base_score -= 0.1
        
        for word in complexity_indicators['low_effort']:
            if word in text_to_analyze:
                base_score += 0.1
        
        # Consider grant amount in effort calculation
        # Larger grants typically require more effort
        if grant.amount:
            amount_threshold = self.config.get('high_effort_amount_threshold', 100000)
            if grant.amount > amount_threshold:
                base_score -= 0.2
        
        # Consider deadline in effort calculation
        # Shorter deadlines mean more concentrated effort
        if grant.deadline:
            days_until_deadline = (grant.deadline - datetime.now()).days
            if days_until_deadline < 14:  # Two weeks
                base_score -= 0.2
        
        # Ensure score stays between 0 and 1
        return max(0.0, min(1.0, base_score))
    
    def score_grant(self, grant: Grant) -> GrantScore:
        """Calculate comprehensive score for a grant."""
        weights = self.config.get('scoring_weights', {
            'relevance': 0.4,
            'amount': 0.2,
            'urgency': 0.2,
            'effort': 0.2
        })
        
        relevance_score = self.calculate_relevance_score(grant)
        amount_score = self.calculate_amount_score(grant)
        urgency_score = self.calculate_urgency_score(grant)
        effort_score = self.calculate_effort_score(grant)
        
        total_score = (
            relevance_score * weights['relevance'] +
            amount_score * weights['amount'] +
            urgency_score * weights['urgency'] +
            effort_score * weights['effort']
        )
        
        return GrantScore(
            grant=grant,
            relevance_score=relevance_score,
            amount_score=amount_score,
            urgency_score=urgency_score,
            effort_score=effort_score,
            total_score=total_score,
            notes=None
        )
    
    def filter_grants(self, grants: List[Grant]) -> List[GrantScore]:
        """
        Filter and score a list of grants.
        
        Args:
            grants: List of grants to analyze
            
        Returns:
            List of scored grants, sorted by total score descending
        """
        scored_grants = []
        for grant in grants:
            try:
                score = self.score_grant(grant)
                if score.total_score >= self.config.get('min_score_threshold', 0.5):
                    scored_grants.append(score)
            except Exception as e:
                self.logger.error(f"Error scoring grant {grant.id}: {str(e)}")
                continue
                
        return sorted(scored_grants, key=lambda x: x.total_score, reverse=True) 