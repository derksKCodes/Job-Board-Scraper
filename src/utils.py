import logging
import time
import random
from functools import wraps
from typing import List, Optional
import pandas as pd
from pathlib import Path
from fake_useragent import UserAgent

from config import DATA_DIR, LOGS_DIR, USER_AGENTS
import random, asyncio
from config import USER_AGENTS, DELAY_RANGE, USE_RANDOM_DELAYS

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
    }

async def human_delay():
    if USE_RANDOM_DELAYS:
        await asyncio.sleep(random.uniform(*DELAY_RANGE))

def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """Set up logger with file and console handlers."""
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler
    file_handler = logging.FileHandler(LOGS_DIR / log_file)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger('scraper', 'scraper.log')

def retry(max_retries: int = 3, delay: int = 5, backoff: int = 2):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Failed after {max_retries} retries: {e}")
                        raise
                    wait_time = delay * (backoff ** (retries - 1))
                    logger.warning(f"Retry {retries}/{max_retries} after {wait_time}s: {e}")
                    time.sleep(wait_time)
        return wrapper
    return decorator

def get_random_user_agent() -> str:
    """Get a random user agent."""
    try:
        ua = UserAgent()
        return ua.random
    except:
        return random.choice(USER_AGENTS)

def normalize_url(url: str) -> str:
    """Normalize URL by removing tracking parameters and standardizing."""
    import urllib.parse as urlparse
    from urllib.parse import urlunparse, parse_qs
    
    # Parse URL
    parsed = urlparse.urlparse(url)
    
    # Remove common tracking parameters
    query_params = parse_qs(parsed.query)
    filtered_params = {k: v for k, v in query_params.items() 
                      if not any(track in k.lower() for track in 
                                ['utm_', 'fbclid', 'gclid', 'msclkid'])}
    
    # Rebuild URL
    new_query = urlparse.urlencode(filtered_params, doseq=True)
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
    
    return normalized

def read_input_file(file_path: Path) -> List[str]:
    """Read URLs from input file (CSV, TXT, or Excel)."""
    urls = []
    
    if not file_path.exists():
        logger.error(f"Input file not found: {file_path}")
        return urls
    
    try:
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
            # Assume URLs are in a column named 'url' or first column
            if 'url' in df.columns:
                urls = df['url'].dropna().tolist()
            else:
                urls = df.iloc[:, 0].dropna().tolist()
                
        elif file_path.suffix.lower() == '.txt':
            with open(file_path, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
                
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
            if 'url' in df.columns:
                urls = df['url'].dropna().tolist()
            else:
                urls = df.iloc[:, 0].dropna().tolist()
                
        else:
            logger.error(f"Unsupported file format: {file_path.suffix}")
            
    except Exception as e:
        logger.error(f"Error reading input file: {e}")
        
    # Normalize URLs
    normalized_urls = [normalize_url(url) for url in urls if url]
    logger.info(f"Read {len(normalized_urls)} URLs from {file_path}")
    
    return normalized_urls