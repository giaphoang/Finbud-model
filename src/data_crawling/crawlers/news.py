import time
import requests
from typing import Dict, List

from aws_lambda_powertools import Logger
from bs4 import BeautifulSoup
from bs4.element import Tag
from config import settings
from core.db.documents import FinancialsDocument
from core.errors import ImproperlyConfigured
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from crawlers.base import BaseAbstractCrawler


logger = Logger(service="llm-twin-course/crawler")

class FinancialsCrawler(BaseAbstractCrawler):

    model = FinancialsDocument

    def __init__(self):
        super().__init__()

    def extract(self) -> None:
        logger.info("Starting news data extraction")
        # Direct to findata
        self.driver.get("https://finbud.pro/docs/aapl")
        time.sleep(5)

        search_ticker_btn = self.driver.find_element(By.CSS_SELECTOR, "div.buttons-header button:nth-of-type(2)")
        search_ticker_btn.click()

        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.search-item")))

        search_items = self.driver.find_elements(By.CSS_SELECTOR, "li.search-item")
        max_search_index = len(search_items)
        
        logger.info(f"Found {max_search_index} search items to process")
        
        body = self.driver.find_element(By.TAG_NAME, "body")
        body.click() # Click on body to defocus input

        # Process each company
        for search_index in range(max_search_index):
            logger.info(f"Processing search item {search_index} of {max_search_index}")
            search_ticker_btn.click()

            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.search-item")))
            logger.info("hello1")
            ticker_item = self.driver.find_elements(By.CSS_SELECTOR, "li.search-item")[search_index]
            ticker_item.click()

            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.data-card:nth-of-type(2) div.card-body div.card-row")))
            rows = self.driver.find_elements(By.CSS_SELECTOR, "div.data-card:nth-of-type(2) div.card-body div.card-row")            
            for row in rows: # Process each row in the table
                link = row.find_element(By.CSS_SELECTOR, "a")
                spans = row.find_elements(By.CSS_SELECTOR, "span")
                company_name = spans[0].text
                quarter = spans[1].text
                date = spans[2].text

                logger.info(f"Processing news data for {company_name} - Quarter: {quarter}, Date: {date}")

                href = link.get_attribute("href")
                logger.debug(f"Fetching data from URL: {href}")
                
                header = {
                    "User-Agent": "Phuc Khang Le personal project phuc.khang.le@gmail.com - fetching EDGAR 10-K filings"
                }

                # Get the content of the document
                response = requests.get(href, headers=header)
                soup = BeautifulSoup(response.text, "html.parser")
                content = ""
                for tag in soup.body.descendants:
                    if tag.name == "table":
                        clean_table = tag.__copy__()
                        for subtag in clean_table.find_all(True):
                            subtag.attrs = {}
                        clean_table.attrs = {}
                        content += "\n\n[TABLE]\n" + str(clean_table) + "\n[/TABLE]\n\n"
                    elif tag.name in ["p", "div"] and tag.get_text(strip=True):
                        content += tag.get_text(strip=True) + "\n"

                data = {
                    "company_name": company_name,
                    "form_type": "news",
                    "content": content,
                    "quarter": quarter,
                    "date": date
                }

                # Save the data to the database
                instance = self.model(
                    company_name=company_name,
                    form_type="news",
                    content=content,
                    quarter=quarter,
                    date=date
                )
                instance.save()
                logger.info(f"Successfully saved news data for {company_name}")
                print(data)
                time.sleep(1)

        logger.info("Finished news data extraction")
        time.sleep(10)  # Wait longer to see the result