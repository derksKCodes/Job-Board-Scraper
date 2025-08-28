import requests
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
from urllib.parse import urljoin, urlparse
import asyncio
import playwright
from playwright.async_api import async_playwright
import random

from utils import logger, retry, get_random_user_agent
from parser import HTMLParser
from config import USE_PROXIES, PROXIES, USE_STEALTH, REQUEST_TIMEOUT

def get_random_headers():
    """Generate random headers for requests."""
    return {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'Referer': 'https://www.google.com/',
    }

async def human_delay():
    """Add human-like delay between requests."""
    await asyncio.sleep(random.uniform(1.0, 3.0))

class JobScraper:
    def __init__(self, use_selenium: bool = False, use_playwright: bool = True):
        self.parser = HTMLParser()
        self.use_selenium = use_selenium
        self.use_playwright = use_playwright
        self.session = requests.Session()
        self.playwright_initialized = False
        self.selenium_initialized = False
        self.browser = None
        self.page = None
        self.playwright = None
        
        # Set realistic headers
        self.session.headers.update(get_random_headers())
        
        if use_selenium:
            self._init_selenium()
            
            # 🔹 Pre-initialize Playwright if enabled
        if use_playwright:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(self.setup_playwright())
    
    def _init_selenium(self) -> None:
        """Initialize Selenium WebDriver with stealth options."""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument(f'--user-agent={get_random_user_agent()}')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(REQUEST_TIMEOUT)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.selenium_initialized = True
            logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            self.use_selenium = False
            self.selenium_initialized = False
            
        # Add this method to your JobScraper class
    async def extract_job_urls_from_search(self, search_url: str) -> List[str]:
        """Extract individual job URLs from a search results page."""
        if not self.playwright_initialized:
            await self.setup_playwright()
        
        try:
            context = await self.browser.new_context(
                user_agent=get_random_user_agent(),
                viewport={'width': 1920, 'height': 1080},
                locale='en-US'
            )
            
            page = await context.new_page()
            await page.goto(search_url, wait_until='domcontentloaded')
            
            # Wait for job listings to load
            await page.wait_for_selector('[class*="job-card"], [class*="result"]', timeout=40000)
            
            # Extract job URLs
            job_urls = await page.evaluate('''() => {
                const links = [];
                // LinkedIn selectors
                document.querySelectorAll('a.base-card__full-link, a.job-card-container__link').forEach(link => {
                    if (link.href && link.href.includes('/jobs/view/')) {
                        links.push(link.href);
                    }
                });
                // Indeed selectors
                document.querySelectorAll('a.jcs-JobTitle, a.jobTitle').forEach(link => {
                    if (link.href) links.push(link.href);
                });
                return links.slice(0, 10); // Limit to first 10 jobs
            }''')
            
            await context.close()
            return job_urls
            
        except Exception as e:
            logger.error(f"Error extracting job URLs from search: {e}")
            return []
    
    async def setup_playwright(self) -> None:
        """Setup Playwright browser with stealth, headers, and proxies."""
        try:
            self.playwright = await async_playwright().start()
            
            # # Use proxy if configured
            # proxy = random.choice(PROXIES) if USE_PROXIES and PROXIES else None
            
            # launch_options = {
            #     'headless': True,
            #     'args': [
            #         '--disable-blink-features=AutomationControlled',
            #         '--disable-web-security',
            #         '--allow-running-insecure-content',
            #         '--no-sandbox',
            #         '--disable-setuid-sandbox',
            #         '--disable-dev-shm-usage'
            #     ]
            # }
            
            # if proxy:
            #     launch_options['proxy'] = {'server': proxy}
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )

            # Open new page with random headers
            self.page = await self.browser.new_page(
                extra_http_headers=get_random_headers()
            )
            
            
            # Create new page with random headers
            self.page = await self.browser.new_page(
                extra_http_headers=get_random_headers()
            )
            
            # Apply stealth techniques if enabled
            if USE_STEALTH:
                await self.enable_stealth()
            
            self.playwright_initialized = True
            logger.info("Playwright browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}")
            self.use_playwright = False
            self.playwright_initialized = False
    
    async def enable_stealth(self):
        """Apply stealth techniques to reduce bot detection."""
        await self.page.add_init_script("""
            // Hide webdriver flag
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            // Fake plugins
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            // Fake languages
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            // Override permissions
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: async () => ({ state: 'granted' })
                })
            });
        """)
    
    @retry(max_retries=2, delay=5)
    def scrape_url(self, url: str) -> Optional[Dict]:
        """Scrape a single job URL."""
        logger.info(f"Scraping: {url}")

        try:
            time.sleep(random.uniform(4, 6))  # human-like delay
            loop = asyncio.get_event_loop()

            # 🔹 Force Playwright first for LinkedIn
            if "linkedin.com" in url and self.use_playwright and self.playwright_initialized:
                html = loop.run_until_complete(self._scrape_with_playwright(url))
                if html and self._is_valid_html(html, url):
                    job_data = self.parser.parse_job_page(html, url)
                    if job_data and job_data.get("job_title"):
                        return job_data
                logger.warning(f"Playwright failed for LinkedIn URL: {url}")
                return None

            # Try requests first
            html = self._scrape_with_requests(url)
            if html and self._is_valid_html(html, url):
                job_data = self.parser.parse_job_page(html, url)
                if job_data and job_data.get("job_title"):
                    return job_data

            # Fallback to Playwright
            if self.use_playwright and self.playwright_initialized:
                html = loop.run_until_complete(self._scrape_with_playwright(url))
                if html and self._is_valid_html(html, url):
                    job_data = self.parser.parse_job_page(html, url)
                    if job_data and job_data.get("job_title"):
                        return job_data

            # Fallback to Selenium
            if self.use_selenium and self.selenium_initialized:
                html = self._scrape_with_selenium(url)
                if html and self._is_valid_html(html, url):
                    job_data = self.parser.parse_job_page(html, url)
                    if job_data and job_data.get("job_title"):
                        return job_data

            logger.warning(f"All scraping methods failed for: {url}")
            return None

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    
    def _is_valid_html(self, html: str, url: str) -> bool:
        """Check if HTML is valid and not a blocking page."""
        if not html or len(html) < 1000:
            return False
        
        # Check for common blocking indicators
        blocking_indicators = [
            "access denied", "captcha", "robot check", 
            "cloudflare", "security check", "distil",
            "unusual traffic", "please verify you are human",
            "enable javascript", "403 forbidden", "404 not found",
            "this page isn't working", "rate limited", "too many requests"
        ]
        
        html_lower = html.lower()
        for indicator in blocking_indicators:
            if indicator in html_lower:
                logger.warning(f"Blocking detected on {url}: {indicator}")
                return False
        
        return True
    
    def _scrape_with_requests(self, url: str) -> Optional[str]:
        """Scrape using requests library with proper headers."""
        try:
            # Add random delay
            time.sleep(random.uniform(0.5, 1.5))
            
            response = self.session.get(url, headers=get_random_headers(), timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Check if we got a valid HTML response
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' in content_type:
                return response.text
            return None
            
        except Exception as e:
            logger.debug(f"Requests failed for {url}: {e}")
            return None
    
    def _scrape_with_selenium(self, url: str) -> Optional[str]:
        """Scrape using Selenium for JavaScript-heavy pages."""
        if not self.selenium_initialized:
            return None
            
        try:
            self.driver.get(url)
            # Wait for page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(3)
            return self.driver.page_source
            
        except Exception as e:
            logger.debug(f"Selenium failed for {url}: {e}")
            return None
    
    async def _scrape_with_playwright(self, url: str) -> Optional[str]:
        """Scrape using Playwright for complex JavaScript pages."""
        if not self.playwright_initialized:
            return None
        
        try:
            context = await self.browser.new_context(
                user_agent=get_random_user_agent(),
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            # Block unnecessary resources to speed up loading
            await context.route("**/*", lambda route: route.abort() 
                if route.request.resource_type in ["image", "stylesheet", "font", "media"] 
                else route.continue_()
            )
            
            page = await context.new_page()
            
            # Set extra HTTP headers
            await page.set_extra_http_headers(get_random_headers())
            
            # Navigate to URL with realistic timing
            await page.goto(url, wait_until='domcontentloaded', timeout=REQUEST_TIMEOUT * 1000)
            
            # Wait for job content to load with realistic pauses
            try:
                await page.wait_for_selector('body', timeout=15000)
                # Add human-like delay
                await asyncio.sleep(random.uniform(2, 4))
            except:
                pass
                
            content = await page.content()
            await context.close()
            return content
            
        except Exception as e:
            logger.debug(f"Playwright failed for {url}: {e}")
            return None
    
    def scrape_multiple_urls(self, urls: List[str]) -> List[Dict]:
        """Scrape multiple URLs with rate limiting."""
        jobs = []
        
        for i, url in enumerate(urls):
            job = self.scrape_url(url)
            if job:
                jobs.append(job)
                logger.info(f"Successfully scraped job: {job.get('job_title', 'Unknown')} at {job.get('company', 'Unknown')}")
            
            # Rate limiting with progressive backoff
            if i < len(urls) - 1:
                sleep_time = 3 + (i % 4)  # Vary between 3-6 seconds
                time.sleep(sleep_time)
        
        return jobs
    
    async def _shutdown_playwright(self):
        """Properly shutdown Playwright resources."""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.warning(f"Playwright shutdown issue: {e}")
    
    def close(self):
        """Clean up resources."""
        try:
            self.session.close()
            if hasattr(self, 'driver') and self.selenium_initialized:
                self.driver.quit()
            if self.playwright_initialized:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self._shutdown_playwright())
        except Exception as e:
            logger.error(f"Error closing scraper resources: {e}")
