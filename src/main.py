import argparse
from typing import List
from datetime import datetime
import sys
import time
import asyncio
from config import INPUT_URLS_FILE, OUTPUT_FORMATS
from utils import read_input_file, logger
from scraper import JobScraper
from deduplicator import Deduplicator
from storage import JobStorage
from scheduler import ScrapingScheduler

def run_scraping():
    """Main scraping function that can be called directly or scheduled."""
    try:
        # Read input URLs
        urls = read_input_file(INPUT_URLS_FILE)
        if not urls:
            logger.error("No URLs found to scrape")
            return False
        
        # Initialize components
        scraper = JobScraper(use_selenium=False, use_playwright=True)
        storage = JobStorage(OUTPUT_FORMATS)
        deduplicator = Deduplicator(storage)
        
        all_job_urls = []
        
        # Separate search URLs from job URLs
        search_urls = [url for url in urls if 'search' in url or 'results' in url]
        job_urls = [url for url in urls if url not in search_urls]
        
        # Extract job URLs from search pages
        if search_urls:
            logger.info(f"Extracting job URLs from {len(search_urls)} search pages")
            loop = asyncio.get_event_loop()
            for search_url in search_urls:
                job_urls_from_search = loop.run_until_complete(
                    scraper.extract_job_urls_from_search(search_url)
                )
                all_job_urls.extend(job_urls_from_search)
                logger.info(f"Found {len(job_urls_from_search)} jobs from {search_url}")
                time.sleep(5)  # Delay between search requests
        
        all_job_urls.extend(job_urls)
        
        if not all_job_urls:
            logger.error("No job URLs found to scrape")
            return False
            
        # Scrape individual job pages
        logger.info(f"Starting to scrape {len(all_job_urls)} job URLs")
        jobs = scraper.scrape_multiple_urls(all_job_urls)
        # Scrape jobs
        logger.info(f"Starting to scrape {len(urls)} URLs")
        jobs = scraper.scrape_multiple_urls(urls)
        
        # Filter duplicates
        unique_jobs = deduplicator.filter_duplicates(jobs)
        
        # Save results to all formats
        if unique_jobs:
            storage.save_jobs(unique_jobs)
            logger.info(f"Successfully processed {len(unique_jobs)} new jobs")
        else:
            logger.info("No new jobs found")
        
        # Clean up
        scraper.close()
        
    except Exception as e:
        logger.error(f"Error in main scraping function: {e}")
        return False
    
    return True

def main():
    """Main entry point for the scraper."""
    parser = argparse.ArgumentParser(description='Job Board Scraper')
    parser.add_argument('--once', action='store_true', 
                       help='Run scraping once and exit')
    parser.add_argument('--schedule', action='store_true',
                       help='Run scraping on a schedule')
    parser.add_argument('--interval', type=int, default=2,
                       help='Scraping interval in hours (default: 2)')
    parser.add_argument('--formats', nargs='+', choices=['csv', 'json', 'excel'], default=OUTPUT_FORMATS,
                       help='Output formats (default: csv json excel)')
    
    args = parser.parse_args()
    
    if not args.once and not args.schedule:
        parser.print_help()
        sys.exit(1)
    
    # Update output formats if specified
    if args.formats != OUTPUT_FORMATS:
        
        OUTPUT_FORMATS.clear()
        OUTPUT_FORMATS.extend(args.formats)
    
    try:
        if args.once:
            logger.info("Running scraper once")
            success = run_scraping()
            sys.exit(0 if success else 1)
        
        elif args.schedule:
            logger.info(f"Starting scraper on {args.interval}-hour schedule")
            scheduler = ScrapingScheduler(run_scraping, args.interval)
            scheduler.start()
            
    except KeyboardInterrupt:
        logger.info("Scraper stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()