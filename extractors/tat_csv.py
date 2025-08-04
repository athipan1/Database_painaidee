"""
TAT (Tourism Authority of Thailand) CSV data extractor.
Downloads CSV data from TAT Open Data and converts to structured format.
"""
import logging
import requests
import pandas as pd
import tempfile
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class TATCSVExtractor:
    """Extractor for TAT Open Data CSV files."""
    
    def __init__(self, csv_url: str, timeout: int = 30):
        """
        Initialize the TAT CSV extractor.
        
        Args:
            csv_url: The TAT CSV download URL
            timeout: Request timeout in seconds
        """
        self.csv_url = csv_url
        self.timeout = timeout
    
    def extract(self) -> List[Dict[str, Any]]:
        """
        Extract data from TAT CSV file.
        
        Returns:
            List of raw CSV data items as dictionaries
            
        Raises:
            requests.RequestException: If CSV download fails
            pd.errors.ParserError: If CSV parsing fails
            Exception: If data extraction fails
        """
        logger.info(f"Extracting TAT CSV data from: {self.csv_url}")
        
        try:
            # Download CSV to temporary file
            temp_file = None
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as f:
                temp_file = f.name
                logger.info("Downloading CSV data...")
                
                response = requests.get(self.csv_url, timeout=self.timeout)
                response.raise_for_status()
                
                f.write(response.content)
                logger.info(f"CSV downloaded successfully, size: {len(response.content)} bytes")
            
            # Read CSV with pandas
            logger.info("Parsing CSV data...")
            try:
                # Try different encodings for Thai text
                for encoding in ['utf-8', 'utf-8-sig', 'tis-620', 'cp874']:
                    try:
                        df = pd.read_csv(temp_file, encoding=encoding)
                        logger.info(f"Successfully parsed CSV with encoding: {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    # If all encodings fail, try with error handling
                    df = pd.read_csv(temp_file, encoding='utf-8', errors='ignore')
                    logger.warning("Used UTF-8 with error handling due to encoding issues")
                
            except Exception as e:
                logger.error(f"Failed to parse CSV: {e}")
                raise
            
            # Clean column names
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
            
            # Convert to list of dictionaries
            raw_data = df.to_dict('records')
            
            logger.info(f"Successfully extracted {len(raw_data)} TAT CSV items")
            logger.info(f"CSV columns: {list(df.columns)}")
            
            return raw_data
            
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                    logger.debug("Temporary CSV file cleaned up")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file: {e}")