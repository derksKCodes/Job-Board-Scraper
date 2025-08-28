import pandas as pd
from typing import List, Dict, Set, Union
from datetime import datetime
import hashlib
import json
from utils import logger
from storage import JobStorage

class Deduplicator:
    def __init__(self, storage: JobStorage):
        self.storage = storage
        self.existing_hashes: Set[str] = set()
        self.load_existing_hashes()
    
    def load_existing_hashes(self) -> None:
        """Load existing job hashes from all output formats."""
        try:
            # Try loading from CSV first
            df = self.storage.load_jobs('csv')
            if not df.empty:
                self._load_hashes_from_dataframe(df)
            
            # Also try loading from JSON
            json_data = self.storage.load_jobs('json')
            if json_data:
                self._load_hashes_from_json(json_data)
                
            logger.info(f"Loaded {len(self.existing_hashes)} existing job hashes")
            
        except Exception as e:
            logger.error(f"Error loading existing jobs: {e}")
    
    def _load_hashes_from_dataframe(self, df: pd.DataFrame) -> None:
        """Load hashes from DataFrame."""
        for _, row in df.iterrows():
            job_hash = self._create_job_hash(
                row.get('job_title', ''),
                row.get('company', ''),
                row.get('location', ''),
                row.get('date_posted', '')
            )
            self.existing_hashes.add(job_hash)
    
    def _load_hashes_from_json(self, json_data: List[Dict]) -> None:
        """Load hashes from JSON data."""
        for job in json_data:
            job_hash = self._create_job_hash(
                job.get('job_title', ''),
                job.get('company', ''),
                job.get('location', ''),
                job.get('date_posted', '')
            )
            self.existing_hashes.add(job_hash)
    
    def _create_job_hash(self, title: str, company: str, location: str, date_posted: str) -> str:
        """Create a unique hash for a job based on key identifiers."""
        hash_string = f"{title}_{company}_{location}_{date_posted}"
        return hashlib.md5(hash_string.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, job_data: Dict) -> bool:
        """Check if a job is a duplicate."""
        job_hash = self._create_job_hash(
            job_data.get('job_title', ''),
            job_data.get('company', ''),
            job_data.get('location', ''),
            job_data.get('date_posted', '')
        )
        return job_hash in self.existing_hashes
    
    def add_job_hash(self, job_data: Dict) -> None:
        """Add a job hash to the existing hashes set."""
        job_hash = self._create_job_hash(
            job_data.get('job_title', ''),
            job_data.get('company', ''),
            job_data.get('location', ''),
            job_data.get('date_posted', '')
        )
        self.existing_hashes.add(job_hash)
    
    def filter_duplicates(self, jobs: List[Dict]) -> List[Dict]:
        """Filter out duplicate jobs from a list."""
        unique_jobs = []
        for job in jobs:
            if not self.is_duplicate(job):
                unique_jobs.append(job)
                self.add_job_hash(job)
        
        logger.info(f"Filtered {len(jobs) - len(unique_jobs)} duplicates, {len(unique_jobs)} unique jobs remaining")
        return unique_jobs