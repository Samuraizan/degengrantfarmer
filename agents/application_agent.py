"""
Application Agent for Degen Grant Farmer.

This module implements the Application Agent responsible for generating
grant applications using AI/LLM technology.
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime
import json
import os
import openai
from pydantic import BaseModel
from .scraper_agent import Grant
from .filter_agent import GrantScore

class ApplicationSection(BaseModel):
    """Data model for a section of a grant application."""
    title: str
    content: str
    word_count: Optional[int]
    max_words: Optional[int]
    status: str = "draft"  # draft, reviewed, final
    feedback: Optional[str]

class Application(BaseModel):
    """Data model for a complete grant application."""
    grant: Grant
    sections: List[ApplicationSection]
    status: str = "in_progress"  # in_progress, ready_for_review, submitted
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    submission_date: Optional[datetime]
    notes: Optional[str]

class ApplicationAgent:
    """Agent responsible for generating grant applications using AI."""
    
    def __init__(self, config: Dict):
        """Initialize the application agent with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        openai.api_key = config.get('openai_api_key')
        
        # Load section templates
        self.section_templates = {
            "Executive Summary": self._load_template("executive_summary"),
            "Project Description": self._load_template("project_description"),
            "Methodology": self._load_template("methodology"),
            "Budget Narrative": self._load_template("budget_narrative"),
            "Team & Qualifications": self._load_template("team_qualifications"),
            "Impact & Outcomes": self._load_template("impact_outcomes")
        }
    
    def _load_template(self, template_name: str) -> str:
        """Load a prompt template for a specific section."""
        templates = {
            "executive_summary": """
            Write an executive summary for a grant application to {grant_title}.
            
            Grant Description:
            {grant_description}
            
            Organization Profile:
            - Name: {org_name}
            - Type: {org_type}
            - Mission: {mission}
            - Core Competencies: {competencies}
            
            Requirements:
            - Maximum words: {max_words}
            - Focus on value proposition and alignment with grant objectives
            - Highlight relevant experience and capabilities
            - Be specific about intended outcomes
            
            Use a professional tone and focus on how the organization's expertise
            aligns with the grant's goals. Emphasize blockchain/Web3 capabilities
            where relevant.
            """,
            
            "project_description": """
            Write a detailed project description for {grant_title}.
            
            Grant Context:
            {grant_description}
            
            Organization Details:
            {org_profile}
            
            Requirements:
            - Maximum words: {max_words}
            - Include clear project goals and objectives
            - Describe the problem being solved
            - Explain the technical approach
            - Highlight innovation and unique value proposition
            
            Focus on technical depth while maintaining clarity. Emphasize how
            blockchain/Web3 technology will be leveraged effectively.
            """,
            
            "methodology": """
            Write a methodology section for {grant_title}.
            
            Project Context:
            {project_description}
            
            Technical Capabilities:
            {competencies}
            
            Requirements:
            - Maximum words: {max_words}
            - Detail technical approach and implementation plan
            - Include timeline and milestones
            - Describe development methodology
            - Address potential challenges and mitigation strategies
            
            Be specific about blockchain/Web3 technologies and development
            practices to be used.
            """,
            
            "budget_narrative": """
            Write a budget narrative for {grant_title}.
            
            Grant Amount: {amount}
            Team Size: {team_size}
            
            Requirements:
            - Maximum words: {max_words}
            - Justify the requested funding amount
            - Break down major cost categories
            - Explain resource allocation
            - Demonstrate cost effectiveness
            
            Focus on realistic blockchain/Web3 development costs and resource
            requirements.
            """,
            
            "team_qualifications": """
            Write a team qualifications section for {grant_title}.
            
            Organization Profile:
            {org_profile}
            
            Previous Grants:
            {previous_grants}
            
            Requirements:
            - Maximum words: {max_words}
            - Highlight relevant team experience
            - Showcase blockchain/Web3 expertise
            - Include previous successful projects
            - Demonstrate capability to deliver
            
            Emphasize successful delivery of previous blockchain/Web3 projects
            and grants.
            """,
            
            "impact_outcomes": """
            Write an impact and outcomes section for {grant_title}.
            
            Grant Context:
            {grant_description}
            
            Project Goals:
            {project_goals}
            
            Requirements:
            - Maximum words: {max_words}
            - Define measurable outcomes
            - Describe expected impact
            - Include success metrics
            - Address sustainability
            
            Focus on both technical and ecosystem impact in the blockchain/Web3
            space.
            """
        }
        return templates.get(template_name, "")
    
    def _format_prompt_variables(self, template: str, grant: Grant, section_title: str) -> str:
        """Format a template with grant and organization details."""
        org_profile = self.config.get('user_profile', {})
        
        variables = {
            'grant_title': grant.title,
            'grant_description': grant.description,
            'org_name': org_profile.get('organization_name', ''),
            'org_type': org_profile.get('organization_type', ''),
            'mission': org_profile.get('mission_statement', ''),
            'competencies': ', '.join(org_profile.get('core_competencies', [])),
            'team_size': org_profile.get('team_size', 0),
            'amount': grant.amount,
            'max_words': self.config.get('section_word_limits', {}).get(section_title, 500),
            'previous_grants': ', '.join(
                f"{g['name']} (${g['amount']:,})"
                for g in org_profile.get('previous_grants', [])
            ),
            'org_profile': json.dumps(org_profile, indent=2),
            'project_goals': "Derived from grant description",  # Could be enhanced
            'project_description': grant.description  # Could be enhanced with generated content
        }
        
        return template.format(**variables)
    
    async def generate_section_content(
        self,
        section_title: str,
        grant: Grant,
        max_words: Optional[int] = None
    ) -> str:
        """
        Generate content for a specific section using LLM.
        
        Args:
            section_title: Title of the section (e.g., "Executive Summary")
            grant: Grant to generate content for
            max_words: Maximum word count if specified
            
        Returns:
            Generated content for the section
        """
        try:
            template = self.section_templates.get(section_title)
            if not template:
                raise ValueError(f"No template found for section: {section_title}")
            
            formatted_prompt = self._format_prompt_variables(template, grant, section_title)
            
            # Call OpenAI API
            response = await openai.ChatCompletion.acreate(
                model=self.config.get('openai_model', 'gpt-4'),
                messages=[
                    {"role": "system", "content": "You are an expert grant writer specializing in blockchain and Web3 projects. Write in a professional, technical, yet clear style."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.7,
                max_tokens=1500,
                presence_penalty=0.1,  # Slight penalty for repetition
                frequency_penalty=0.1   # Slight penalty for frequent tokens
            )
            
            content = response.choices[0].message.content.strip()
            
            # Check word count and truncate if needed
            if max_words:
                words = content.split()
                if len(words) > max_words:
                    content = ' '.join(words[:max_words]) + '...'
            
            return content
            
        except Exception as e:
            self.logger.error(f"Error generating content for {section_title}: {str(e)}")
            raise
    
    async def generate_application(self, grant: Grant) -> Application:
        """
        Generate a complete grant application.
        
        Args:
            grant: Grant to generate application for
            
        Returns:
            Complete application with all sections
        """
        sections = []
        
        # Order of sections matters for coherent application
        section_titles = [
            "Executive Summary",
            "Project Description",
            "Methodology",
            "Team & Qualifications",
            "Budget Narrative",
            "Impact & Outcomes"
        ]
        
        for title in section_titles:
            try:
                content = await self.generate_section_content(
                    title,
                    grant,
                    max_words=self.config.get('section_word_limits', {}).get(title)
                )
                
                sections.append(ApplicationSection(
                    title=title,
                    content=content,
                    word_count=len(content.split()),
                    max_words=self.config.get('section_word_limits', {}).get(title),
                    status="draft"
                ))
                
            except Exception as e:
                self.logger.error(f"Failed to generate {title}: {str(e)}")
                # Continue with other sections
                continue
        
        application = Application(
            grant=grant,
            sections=sections,
            status="in_progress"
        )
        
        # Save application to file
        await self._save_application(application)
        
        return application
    
    async def _save_application(self, application: Application) -> None:
        """Save application to file system."""
        try:
            # Create application directory
            app_dir = os.path.join(
                self.config.get('storage', {}).get('applications_dir', 'data/applications'),
                f"{application.grant.source}_{application.grant.id}"
            )
            os.makedirs(app_dir, exist_ok=True)
            
            # Save application metadata
            metadata = {
                'grant_id': application.grant.id,
                'grant_title': application.grant.title,
                'status': application.status,
                'created_at': application.created_at.isoformat(),
                'updated_at': application.updated_at.isoformat()
            }
            
            with open(os.path.join(app_dir, 'metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Save each section as a separate file
            for section in application.sections:
                filename = f"{section.title.lower().replace(' ', '_')}.md"
                with open(os.path.join(app_dir, filename), 'w') as f:
                    f.write(f"# {section.title}\n\n")
                    f.write(f"Status: {section.status}\n")
                    f.write(f"Word Count: {section.word_count}")
                    if section.max_words:
                        f.write(f"/{section.max_words}")
                    f.write("\n\n")
                    f.write(section.content)
            
        except Exception as e:
            self.logger.error(f"Error saving application: {str(e)}")
            raise
    
    async def process_grants(self, scored_grants: List[GrantScore]) -> List[Application]:
        """
        Process a list of scored grants and generate applications.
        
        Args:
            scored_grants: List of scored grants to process
            
        Returns:
            List of generated applications
        """
        applications = []
        
        for scored_grant in scored_grants:
            if scored_grant.total_score >= self.config.get('application_threshold', 0.7):
                try:
                    self.logger.info(
                        f"Generating application for {scored_grant.grant.id} "
                        f"(score: {scored_grant.total_score:.2f})"
                    )
                    
                    application = await self.generate_application(scored_grant.grant)
                    applications.append(application)
                    
                    self.logger.info(
                        f"Successfully generated application with "
                        f"{len(application.sections)} sections"
                    )
                    
                except Exception as e:
                    self.logger.error(
                        f"Failed to generate application for {scored_grant.grant.id}: {str(e)}"
                    )
                    continue
        
        return applications 