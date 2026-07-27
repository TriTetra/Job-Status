"""Portfolio website crawler for evidence extraction."""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PortfolioCrawler:
    """Crawl portfolio websites to extract project and skill evidence."""
    
    # Common technology keywords to look for
    TECH_KEYWORDS = [
        # Languages
        "python", "javascript", "typescript", "go", "rust", "java", "c++", "ruby",
        # Frameworks
        "react", "vue", "angular", "next.js", "django", "flask", "fastapi", "express",
        # Databases
        "postgresql", "mongodb", "redis", "mysql", "elasticsearch",
        # Cloud & DevOps
        "aws", "gcp", "azure", "docker", "kubernetes", "terraform",
        # ML/AI
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
        # Tools
        "git", "graphql", "rest api", "microservices"
    ]
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "AplioBot/1.0 (Career Intelligence Platform)"
        }
    
    def crawl(self, url: str) -> dict:
        """
        Crawl portfolio website and extract evidence.
        
        Args:
            url: Portfolio website URL
            
        Returns:
            {
                "projects": [...],
                "technologies": [...],
                "about": "...",
                "error": "..." (if failed)
            }
        """
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {"error": "Invalid URL format"}
            
            # Fetch homepage
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract text content
            text_content = soup.get_text(separator=' ', strip=True).lower()
            
            # Find technologies mentioned
            found_techs = []
            for tech in self.TECH_KEYWORDS:
                if tech.lower() in text_content:
                    found_techs.append(tech)
            
            # Try to find projects section
            projects = self._extract_projects(soup, text_content)
            
            # Try to find about section
            about = self._extract_about(soup)
            
            return {
                "projects": projects,
                "technologies": found_techs,
                "about": about,
                "url": url
            }
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout crawling {url}")
            return {"error": "Request timeout"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error crawling {url}: {e}")
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error crawling {url}: {e}")
            return {"error": f"Crawling failed: {str(e)}"}
    
    def _extract_projects(self, soup: BeautifulSoup, text: str) -> list[dict]:
        """Try to extract project information from portfolio."""
        projects = []
        
        # Look for common project section patterns
        project_sections = soup.find_all(
            ['section', 'div'],
            class_=lambda x: x and any(
                keyword in str(x).lower() 
                for keyword in ['project', 'work', 'portfolio', 'case-study']
            )
        )
        
        for section in project_sections[:5]:  # Limit to 5 projects
            # Try to find project title
            title_elem = section.find(['h2', 'h3', 'h4'])
            if title_elem:
                project_name = title_elem.get_text(strip=True)
                
                # Try to find description
                desc_elem = section.find('p')
                description = desc_elem.get_text(strip=True) if desc_elem else ""
                
                # Find technologies in this project section
                section_text = section.get_text(separator=' ', strip=True).lower()
                project_techs = [
                    tech for tech in self.TECH_KEYWORDS 
                    if tech.lower() in section_text
                ]
                
                projects.append({
                    "name": project_name,
                    "description": description[:200],  # Limit length
                    "technologies": project_techs
                })
        
        return projects
    
    def _extract_about(self, soup: BeautifulSoup) -> Optional[str]:
        """Try to extract about section."""
        # Look for about section
        about_section = soup.find(
            ['section', 'div'],
            class_=lambda x: x and 'about' in str(x).lower()
        )
        
        if about_section:
            text = about_section.get_text(separator=' ', strip=True)
            return text[:500]  # Limit length
        
        return None
