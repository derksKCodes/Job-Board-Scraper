import pandas as pd
from pathlib import Path
from typing import List, Dict, Union
from datetime import datetime
import os
import json
from utils import logger
from config import OUTPUT_CSV_FILE, OUTPUT_JSON_FILE, OUTPUT_EXCEL_FILE, OUTPUT_FORMATS

class JobStorage:
    def __init__(self, output_formats: List[str] = OUTPUT_FORMATS):
        self.output_formats = output_formats
        self.output_files = {
            'csv': OUTPUT_CSV_FILE,
            'json': OUTPUT_JSON_FILE,
            'excel': OUTPUT_EXCEL_FILE
        }
        self.ensure_output_files()
    
    def ensure_output_files(self) -> None:
        """Ensure output files exist with proper structure."""
        for format in self.output_formats:
            if format == 'csv' and not self.output_files['csv'].exists():
                self._create_empty_csv()
            elif format == 'json' and not self.output_files['json'].exists():
                self._create_empty_json()
            # Excel files are created on demand, no need for empty template
    
    def _create_empty_csv(self) -> None:
        """Create empty CSV file with headers."""
        columns = [
            'job_title', 'company', 'location', 'work_setting', 
            'job_type', 'company_logo', 'job_description', 
            'requirements', 'application_url', 'date_posted', 
            'date_collected', 'source_url'
        ]
        df = pd.DataFrame(columns=columns)
        df.to_csv(self.output_files['csv'], index=False, encoding='utf-8')
        logger.info(f"Created new CSV output file: {self.output_files['csv']}")
    
    def _create_empty_json(self) -> None:
        """Create empty JSON file."""
        with open(self.output_files['json'], 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2, ensure_ascii=False)
        logger.info(f"Created new JSON output file: {self.output_files['json']}")
    
    def save_jobs(self, jobs: List[Dict]) -> None:
        """Save jobs to all configured output formats."""
        if not jobs:
            logger.info("No jobs to save")
            return
        
        try:
            # Convert to DataFrame for CSV and Excel formats
            df_new = pd.DataFrame(jobs)
            
            for format in self.output_formats:
                if format == 'csv':
                    self._save_csv(df_new)
                elif format == 'json':
                    self._save_json(jobs)
                elif format == 'excel':
                    self._save_excel(df_new)
                    
            logger.info(f"Saved {len(jobs)} jobs to {len(self.output_formats)} format(s)")
            
        except Exception as e:
            logger.error(f"Error saving jobs: {e}")
    
    def _save_csv(self, df_new: pd.DataFrame) -> None:
        """Save jobs to CSV file."""
        try:
            output_file = self.output_files['csv']
            
            # Read existing data if file exists and has content
            if output_file.exists() and os.path.getsize(output_file) > 0:
                df_existing = pd.read_csv(output_file)
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                df_combined = df_new
            
            # Save to CSV
            df_combined.to_csv(output_file, index=False, encoding='utf-8')
            logger.info(f"Saved {len(df_new)} jobs to CSV: {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
    
    def _save_json(self, jobs: List[Dict]) -> None:
        """Save jobs to JSON file."""
        try:
            output_file = self.output_files['json']
            
            # Read existing data if file exists and has content
            if output_file.exists() and os.path.getsize(output_file) > 0:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_jobs = json.load(f)
                combined_jobs = existing_jobs + jobs
            else:
                combined_jobs = jobs
            
            # Save to JSON with pretty formatting
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(combined_jobs, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Saved {len(jobs)} jobs to JSON: {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
    
    def _save_excel(self, df_new: pd.DataFrame) -> None:
        """Save jobs to Excel file."""
        try:
            output_file = self.output_files['excel']
            
            # Read existing data if file exists
            if output_file.exists():
                df_existing = pd.read_excel(output_file)
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                df_combined = df_new
            
            # Save to Excel with auto column width adjustment
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                df_combined.to_excel(writer, index=False, sheet_name='Jobs')
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Jobs']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            logger.info(f"Saved {len(df_new)} jobs to Excel: {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving to Excel: {e}")
    
    def load_jobs(self, format: str = 'csv') -> Union[pd.DataFrame, List[Dict]]:
        """Load jobs from specified format."""
        try:
            if format == 'csv' and self.output_files['csv'].exists() and os.path.getsize(self.output_files['csv']) > 0:
                return pd.read_csv(self.output_files['csv'])
            elif format == 'json' and self.output_files['json'].exists() and os.path.getsize(self.output_files['json']) > 0:
                with open(self.output_files['json'], 'r', encoding='utf-8') as f:
                    return json.load(f)
            elif format == 'excel' and self.output_files['excel'].exists():
                return pd.read_excel(self.output_files['excel'])
            else:
                if format == 'csv':
                    return pd.DataFrame()
                else:
                    return []
        except Exception as e:
            logger.error(f"Error loading jobs from {format}: {e}")
            if format == 'csv':
                return pd.DataFrame()
            else:
                return []