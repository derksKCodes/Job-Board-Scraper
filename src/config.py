import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Path configurations
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
INPUT_URLS_FILE = DATA_DIR / "input_urls.csv"
OUTPUT_CSV_FILE = DATA_DIR / "jobs.csv"
OUTPUT_JSON_FILE = DATA_DIR / "jobs.json"
OUTPUT_EXCEL_FILE = DATA_DIR / "jobs.xlsx"

# Output format configuration
OUTPUT_FORMATS = ['csv', 'json', 'excel']  # Formats to save

# Scraping configurations
SCRAPING_INTERVAL_HOURS = 2
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
REQUEST_TIMEOUT = 30  # seconds
CONCURRENT_REQUESTS = 5


# Scraping anti-detection settings
USE_PROXIES = True
PROXIES = [
    "http://user:pass@proxy1:port",
    "http://user:pass@proxy2:port",
]

USE_RANDOM_DELAYS = True
DELAY_RANGE = (2, 6)  # seconds

USE_STEALTH = True


# User agent rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
]

# Job board specific selectors (to be extended)
JOB_BOARD_SELECTORS = {
      "simplyhired": {
        "title": "a.jobposting-title",
        "company": "span.jobposting-company",
        "location": "span.jobposting-location",
        "description": "div.jobposting-snippet",
        "date_posted": "span.jobposting-date",
        "url": "a.jobposting-title"
    },
    "wellfound": {
        "title": "a.styles_title__EyX8U",
        "company": "div.styles_company__aM2ke",
        "location": "div.styles_location__NMX1W",
        "description": "div.styles_description__Otby1",
        "date_posted": "div.styles_posted__rp8r7",
        "url": "a.styles_title__EyX8U"
    },
    "indeed": {
        "title": "h2.jobTitle",
        "company": "span.companyName",
        "location": "div.companyLocation",
        "description": "div.job-snippet",
        "date_posted": "span.date",
        "url": "a.jcs-JobTitle"
    },
    "linkedin": {
        "title": "h3.base-search-card__title",
        "company": "h4.base-search-card__subtitle",
        "location": "span.job-search-card__location",
        "description": "div.description__text",
        "date_posted": "time",
        "url": "a.base-card__full-link"
    },
    "glassdoor": {
        "title": "h2.jobTitle",
        "company": "span.employerName",
        "location": "div.location",
        "description": "div.jobDescriptionContent",
        "date_posted": "span.job-posted-date",
        "url": "a.jobLink"
    },
    "ziprecruiter": {
        "title": "h2.job_title",
        "company": "div.company_name",
        "location": "div.job_location",
        "description": "div.job_snippet",
        "date_posted": "time",
        "url": "a.job_link"
    },
    "monster": {
        "title": "h2.title",
        "company": "div.company",
        "location": "div.location",
        "description": "div.summary",
        "date_posted": "time",
        "url": "a.job-link"
    },
    "careerbuilder": {
        "title": "h2.job-title",
        "company": "div.data-results-company",
        "location": "div.data-results-location",
        "description": "div.data-results-snippet",
        "date_posted": "div.data-results-publish-time",
        "url": "a.data-results-content"
    },
    "weworkremotely": {
        "title": "span.title",
        "company": "span.company",
        "location": "span.region",
        "description": "div.listing-container",
        "date_posted": "time",
        "url": "a.listing"
    },
    "flexjobs": {
        "title": "span.job-title",
        "company": "span.job-company",
        "location": "span.job-location",
        "description": "div.job-description",
        "date_posted": "span.job-age",
        "url": "a.job-link"
    },
    "usajobs": {
        "title": "h2.usajobs-search-result--core-heading",
        "company": "h3.usajobs-search-result--agency",
        "location": "span.usajobs-search-result--location",
        "description": "div.usajobs-search-result--summary",
        "date_posted": "span.usajobs-search-result--open-date",
        "url": "a.usajobs-search-result--core"
    },
    "adzuna": {
        "title": "a.job-title",
        "company": "div.company",
        "location": "div.location",
        "description": "div.snippet",
        "date_posted": "span.date",
        "url": "a.job-title"
    },
    "wayup": {
        "title": "h2.job-title",
        "company": "div.job-company",
        "location": "div.job-location",
        "description": "div.job-description",
        "date_posted": "time",
        "url": "a.job-link"
    },
    "handshake": {
        "title": "h3.job-title",
        "company": "div.job-employer",
        "location": "div.job-location",
        "description": "div.job-description",
        "date_posted": "time",
        "url": "a.job-link"
    },
    "collegerecruiter": {
        "title": "h2.job-title",
        "company": "span.company",
        "location": "span.location",
        "description": "div.job-snippet",
        "date_posted": "span.posted",
        "url": "a.job-link"
    },
    "ai-jobs": {
        "title": "h2.job-title",
        "company": "div.company",
        "location": "div.location",
        "description": "div.description",
        "date_posted": "time",
        "url": "a.job-link"
    },
    "jobberman": {
        "title": "h3.job-title",
        "company": "span.company-name",
        "location": "span.job-location",
        "description": "div.job-description",
        "date_posted": "span.job-date",
        "url": "a.job-link"
    },
    "jobstreet": {
        "title": "h3.job-title",
        "company": "span.company-name",
        "location": "span.job-location",
        "description": "div.job-description",
        "date_posted": "span.job-date",
        "url": "a.job-link"
    }
}



# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)