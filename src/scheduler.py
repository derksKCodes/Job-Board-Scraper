from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import time
import signal
import sys
from typing import Callable
from datetime import datetime

from utils import logger
from config import SCRAPING_INTERVAL_HOURS

class ScrapingScheduler:
    def __init__(self, scraping_function: Callable, interval_hours: int = SCRAPING_INTERVAL_HOURS):
        self.scraping_function = scraping_function
        self.interval_hours = interval_hours
        self.scheduler = BackgroundScheduler()
        self.is_running = False
    
    def start(self) -> None:
        """Start the scheduling service."""
        try:
            # Add job to scheduler
            trigger = IntervalTrigger(hours=self.interval_hours)
            self.scheduler.add_job(
                self._run_scraping,
                trigger=trigger,
                id='job_scraping',
                name='Job Board Scraping',
                replace_existing=True
            )
            
            # Run immediately on start
            self._run_scraping()
            
            # Set up signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Start scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info(f"Scheduler started. Running every {self.interval_hours} hours.")
            
            # Keep main thread alive
            while self.is_running:
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            self.stop()
    
    def _run_scraping(self) -> None:
        """Run the scraping function with error handling."""
        try:
            logger.info("Starting scheduled scraping run")
            start_time = time.time()
            
            self.scraping_function()
            
            elapsed = time.time() - start_time
            logger.info(f"Scraping run completed in {elapsed:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error during scheduled scraping: {e}")
    
    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def stop(self) -> None:
        """Stop the scheduling service."""
        if self.scheduler.running:
            self.scheduler.shutdown()
        self.is_running = False
        logger.info("Scheduler stopped")