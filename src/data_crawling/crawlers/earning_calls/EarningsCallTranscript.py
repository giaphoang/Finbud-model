import time
import requests
import re
import json
import os
from typing import Dict, List
import random
from datetime import datetime

from aws_lambda_powertools import Logger
from bs4 import BeautifulSoup
from bs4.element import Tag
from config import settings
from core.db.documents import EarningsCallTranscriptDocument
from core.errors import ImproperlyConfigured
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from crawlers.base import BaseAbstractCrawler


logger = Logger(service="llm-twin-course/crawler")

class EarningsCallTranscriptCrawler(BaseAbstractCrawler):
    model = EarningsCallTranscriptDocument
    
    API_NINJAS_KEY = "1zlzE291cR13yJSELO+0yg==dRIZyGVRofISt6Ep"
    API_NINJAS_URL = "https://api.api-ninjas.com/v1/earningstranscript"
    
    # Predefined list of companies
    COMPANIES = [
        'V', 'XOM', 'MCD', 'SHEL', 'GS', 'TTE', 'BA', 'EADSY', 'TD', 'GEV',
        'BTI', 'SMFG', 'APO', 'MMM', 'IBKR', 'PBR', 'NOC', 'MPLX', 'COIN',
        'TRP', 'SRE', 'ALC', 'AXON', 'E', 'TEL', 'NET', 'FLUT', 'PCG', 'CBRE',
        'XYZ', 'BIDU', 'NVZMY', 'EQT', 'MDY', 'MRAAY', 'YAHOY', 'LPLA',
        'BRK-B', 'PG', 'ACN', 'RTX', 'UNP', 'SAN', 'MO', 'CTAS', 'SHW',
        'TDG', 'NGG', 'DEO', 'SPG'
    ]
    
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update({
            'X-Api-Key': self.API_NINJAS_KEY,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        })

    def get_transcript(self, ticker: str, year: int, quarter: int) -> Dict:
        """Get earnings call transcript for a specific company, year, and quarter"""
        try:
            response = self.session.get(
                self.API_NINJAS_URL,
                params={
                    'ticker': ticker,
                    'year': year,
                    'quarter': quarter
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.info(f"No transcript found for {ticker} {year} Q{quarter}")
                return None
            logger.error(f"HTTP error getting transcript for {ticker} {year} Q{quarter}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting transcript for {ticker} {year} Q{quarter}: {e}")
            return None

    def extract(self) -> None:
        logger.info("Starting earnings call transcript extraction")
        
        current_year = datetime.now().year
        current_quarter = (datetime.now().month - 1) // 3 + 1

        for company in self.COMPANIES:
            logger.info(f"Processing company: {company}")
            
            # Try to get transcripts for current year and previous year
            for year in range(current_year, current_year - 2, -1):
                # For current year, only process up to current quarter
                max_quarter = current_quarter if year == current_year else 4
                
                for quarter in range(1, max_quarter + 1):
                    logger.info(f"Getting transcript for {company} {year} Q{quarter}")
                    
                    # Add delay between requests to avoid rate limiting
                    time.sleep(random.uniform(1, 2))
                    
                    transcript_data = self.get_transcript(company, year, quarter)
                    if not transcript_data:
                        continue

                    try:
                        # Create document instance
                        instance = self.model(
                            source="api_ninjas",
                            url=f"https://api.api-ninjas.com/v1/earningstranscript?ticker={company}&year={year}&quarter={quarter}",
                            title=f"{company} Earnings Call Transcript Q{quarter} {year}",
                            date=transcript_data.get('date', ''),
                            content=transcript_data.get('transcript', '')
                        )
                        instance.save()
                        logger.info(f"Saved transcript for {company} {year} Q{quarter}")
                    except Exception as e:
                        logger.error(f"Error saving transcript for {company} {year} Q{quarter}: {e}")
                        continue

        logger.info("Finished earnings call transcript extraction")
