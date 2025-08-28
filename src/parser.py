from bs4 import BeautifulSoup
import re
from typing import Dict, Optional, List
from urllib.parse import urljoin, urlparse
from datetime import datetime
from utils import logger
from config import JOB_BOARD_SELECTORS

class HTMLParser:
    def __init__(self):
        self.job_board_patterns = {
            'indeed': r'indeed\.com',
            'linkedin': r'linkedin\.com',
            'glassdoor': r'glassdoor\.com',
            'monster': r'monster\.com',
            'careerbuilder': r'careerbuilder\.com'
        }
    
    def detect_job_board(self, url: str) -> Optional[str]:
        """Detect which job board a URL belongs to."""
        for board, pattern in self.job_board_patterns.items():
            if re.search(pattern, url, re.IGNORECASE):
                return board
        return None
    
    def parse_job_page(self, html: str, url: str) -> Dict:
        """Parse job details from HTML content."""
        soup = BeautifulSoup(html, 'lxml')
        job_board = self.detect_job_board(url)
        
        job_data = {
            'job_title': '',
            'company': '',
            'location': '',
            'work_setting': '',
            'job_type': '',
            'company_logo': '',
            'job_description': '',
            'requirements': '',
            'application_url': url,
            'date_posted': '',
            'date_collected': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source_url': url
        }
        
        # First check if this is a job listing page or search results page
        if self._is_search_results_page(soup, url):
            logger.warning(f"URL appears to be search results, not job detail: {url}")
            return job_data  # Return empty data for search result pages
        
        # Use job board specific selectors if available
        if job_board and job_board in JOB_BOARD_SELECTORS:
            parsed_data = self._parse_with_selectors(soup, JOB_BOARD_SELECTORS[job_board])
            job_data.update(parsed_data)
        else:
            # Fallback to generic parsing
            parsed_data = self._parse_generic(soup)
            job_data.update(parsed_data)
        
        # Clean and normalize data
        job_data = self._clean_job_data(job_data)
        
        return job_data
    
    def _is_search_results_page(self, soup: BeautifulSoup, url: str) -> bool:
        """Check if the page is a search results page rather than job detail."""
        # Check URL patterns for search results
        search_patterns = [
            r'search',
            r'jobs\?',
            r'results',
            r'\.com/jobs/',
            r'\.com/\?',
            r'start=\d+',
            r'page=\d+'
        ]
        
        for pattern in search_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        # Check page content for multiple job listings
        job_cards = soup.find_all(attrs={'class': re.compile(r'job|card|listing|result', re.IGNORECASE)})
        if len(job_cards) > 3:
            return True
        
        # Check for pagination elements
        pagination = soup.find(attrs={'class': re.compile(r'pagination|next|page', re.IGNORECASE)})
        if pagination:
            return True
            
        return False
    
    def _parse_with_selectors(self, soup: BeautifulSoup, selectors: Dict) -> Dict:
        """Parse job data using CSS selectors."""
        result = {}
        
        for field, selector in selectors.items():
            try:
                if field == 'url':
                    element = soup.select_one(selector)
                    if element and element.get('href'):
                        result['application_url'] = urljoin('https://www.indeed.com', element['href'])
                else:
                    element = soup.select_one(selector)
                    if element:
                        result[field] = element.get_text(strip=True)
            except Exception as e:
                logger.debug(f"Error parsing {field} with selector {selector}: {e}")
        
        return result
    
    def _parse_generic(self, soup: BeautifulSoup) -> Dict:
        """Generic parsing fallback when no specific selectors are available."""
        result = {}
        logo_selectors = [
            'meta[property="og:image"]',
            'img[alt*="logo"]',
            '.company-logo img'
        ]
        logo = self._find_with_selectors(soup, logo_selectors, get_text=False)
        if logo:
            if logo.has_attr('content'):
                result['company_logo'] = logo['content']
            elif logo.has_attr('src'):
                result['company_logo'] = urljoin(url, logo['src'])

        
        requirements_selectors = [
        '[class*="requirements"]',
        '.job-requirements',
        'section.requirements',
        'ul li'
        ]
        result['requirements'] = self._find_with_selectors(soup, requirements_selectors, get_text=False)
        if result['requirements']:
            result['requirements'] = result['requirements'].get_text(" ", strip=True)


        # Try to find job title - look for h1, h2, or meta tags
        title_selectors = [
            'h1', 'h2',
            'meta[property="og:title"]',
            'meta[name="title"]',
            '[class*="job"][class*="title"]',
            '[class*="position"][class*="title"]',
            '.job-title', '.job_title', '.position-title',
            'title'
        ]
        result['job_title'] = self._find_with_selectors(soup, title_selectors)
        
        # Try to find company - look for company name elements
        company_selectors = [
            '[class*="company"][class*="name"]',
            '[class*="employer"][class*="name"]',
            '.company', '.employer', '.company-name',
            '[itemprop="hiringOrganization"]',
            'meta[property="og:company"]',
            'meta[name="company"]'
        ]
        result['company'] = self._find_with_selectors(soup, company_selectors)
        
        # Try to find location
        location_selectors = [
            '[class*="location"]',
            '[class*="address"]',
            '.location', '.job-location',
            '[itemprop="jobLocation"]',
            'meta[property="og:location"]',
            'meta[name="location"]'
        ]
        result['location'] = self._find_with_selectors(soup, location_selectors)
        
        # Try to find description - get the main content
        description_selectors = [
            '[class*="description"]',
            '[class*="desc"]',
            '.job-description', '.job-desc',
            '[itemprop="description"]',
            'div.description',
            'main', 'article', '.content'
        ]
        result['job_description'] = self._find_with_selectors(soup, description_selectors, get_text=False)
        if result['job_description']:
            result['job_description'] = result['job_description'].get_text(strip=True)
        
        # Try to find date posted
        date_selectors = [
            '[class*="date"]',
            '[class*="time"]',
            '[class*="posted"]',
            '.date-posted', '.post-date',
            '[datetime]',
            'time'
        ]
        result['date_posted'] = self._find_with_selectors(soup, date_selectors)
        
        return result
    
    def _find_with_selectors(self, soup: BeautifulSoup, selectors: list, get_text: bool = True) -> str:
        """Try multiple selectors to find an element."""
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    if get_text:
                        return element.get_text(strip=True)
                    else:
                        return element
            except:
                continue
        return ''
    
    def _clean_job_data(self, job_data: Dict) -> Dict:
        """Clean and normalize job data."""
        cleaned = job_data.copy()
        
        # Clean text fields
        text_fields = ['job_title', 'company', 'location', 'job_description', 'requirements', 'date_posted']
        for field in text_fields:
            if field in cleaned and cleaned[field]:
                cleaned[field] = ' '.join(cleaned[field].split())
        
        # Detect work setting from location or description
        location_text = (cleaned.get('location', '') + ' ' + cleaned.get('job_description', '')).lower()
        if any(term in location_text for term in ['remote', 'work from home', 'wfh', 'virtual', 'telecommute']):
            cleaned['work_setting'] = 'remote'
        elif any(term in location_text for term in ['hybrid', 'partially remote', 'flexible', 'part remote']):
            cleaned['work_setting'] = 'hybrid'
        else:
            cleaned['work_setting'] = 'in-person'
        
        # Detect job type from description
        desc_text = cleaned.get('job_description', '').lower()
        if any(term in desc_text for term in ['full.time', 'full time', 'full-time', 'fulltime']):
            cleaned['job_type'] = 'full-time'
        elif any(term in desc_text for term in ['part.time', 'part time', 'part-time', 'parttime']):
            cleaned['job_type'] = 'part-time'
        elif any(term in desc_text for term in ['contract', 'freelance', 'consultant', 'contractor']):
            cleaned['job_type'] = 'contract'
        elif any(term in desc_text for term in ['internship', 'intern', 'trainee']):
            cleaned['job_type'] = 'internship'
        elif any(term in desc_text for term in ['temporary', 'temp']):
            cleaned['job_type'] = 'temporary'
        else:
            cleaned['job_type'] = 'unknown'
        
        return cleaned