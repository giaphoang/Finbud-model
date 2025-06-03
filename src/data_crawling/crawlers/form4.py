import time
import requests
import re
from typing import Dict, List

from aws_lambda_powertools import Logger
from bs4 import BeautifulSoup
from bs4.element import Tag
from config import settings
from core.db.documents import EdgarFillingDocument
from core.errors import ImproperlyConfigured
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from crawlers.base import BaseAbstractCrawler


logger = Logger(service="llm-twin-course/crawler")

class Form4Crawler(BaseAbstractCrawler):

    model = EdgarFillingDocument

    def __init__(self):
        super().__init__()

    def extract(self) -> None:
        logger.info("Starting Form 4 data extraction")
        # Direct to findata
        self.driver.get("https://finbud.pro/docs/aapl")
        time.sleep(5)

        search_ticker_btn = self.driver.find_element(By.CSS_SELECTOR, "div.buttons-header button:nth-of-type(2)")
        search_ticker_btn.click()

        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.search-item")))

        search_items = self.driver.find_elements(By.CSS_SELECTOR, "li.search-item")
        max_search_index = len(search_items)
        print("max_search_index", max_search_index)
        logger.info(f"Found {max_search_index} search items to process")
        
        body = self.driver.find_element(By.TAG_NAME, "body")
        body.click() # Click on body to defocus input

        # Process each company
        for search_index in range(50):
        # for search_index in range(1):
            logger.info(f"Processing search item {search_index} of {max_search_index}")
            search_ticker_btn.click()

            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.search-item")))
            logger.info("hello1")
            ticker_item = self.driver.find_elements(By.CSS_SELECTOR, "li.search-item")[search_index]
            ticker_item.click()

            try:
                # Increase wait time to 20 seconds for better reliability
                wait = WebDriverWait(self.driver, 20)
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.data-card:nth-of-type(4) div.card-body div.card-row")))
                
                # Add a small delay to ensure content is fully loaded
                time.sleep(2)
                
                rows = self.driver.find_elements(By.CSS_SELECTOR, "div.data-card:nth-of-type(4) div.card-body div.card-row")
                
                # Log the actual HTML content for debugging
                logger.info(f"Data card content: {self.driver.find_element(By.CSS_SELECTOR, 'div.data-card:nth-of-type(1) div.card-body').get_attribute('innerHTML')}")
                
                if not rows:
                    logger.warning(f"No rows found for ticker at index {search_index}, but data card exists. HTML content logged above.")
                    continue
                    
                logger.info(f"Found {len(rows)} rows to process")
            except Exception as e:
                logger.error(f"Error processing ticker at index {search_index}: {str(e)}")
                logger.error(f"Current URL: {self.driver.current_url}")
                # Take a screenshot for debugging
                try:
                    screenshot_path = f"error_screenshot_{search_index}.png"
                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"Error screenshot saved to {screenshot_path}")
                except Exception as screenshot_error:
                    logger.error(f"Failed to save screenshot: {str(screenshot_error)}")
                continue
            
            for row in rows: # Process each row in the table
                try:
                    if row.find_element(By.CSS_SELECTOR, "a").text != "10-K":
                        continue
                    
                    link = row.find_element(By.CSS_SELECTOR, "a")
                    spans = row.find_elements(By.CSS_SELECTOR, "span")
                    
                    ticker = spans[0].text
                    date = spans[2].text

                    logger.info(f"Processing financials data for {ticker} - Date: {date}")

                    href = link.get_attribute("href")
                    logger.info(f"Fetching data from URL: {href}")
                    
                    header = {
                        "User-Agent": "Phuc Khang Le personal project phuc.khang.le@gmail.com - fetching EDGAR 10-K filings"
                    }

                    # Get the content of the document
                    logger.info("Making HTTP request to fetch document...")
                    response = requests.get(href, headers=header)
                    logger.info(f"Response status code: {response.status_code}")
                    
                    if response.status_code != 200:
                        logger.error(f"Failed to fetch data from {href}. Status code: {response.status_code}")
                        continue

                    logger.info("Parsing HTML content...")
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    logger.info("Extracting content from HTML...")
                    content = self.extract_content_from_html(soup)
                    logger.info(f"Extracted content length: {len(content)} characters")


                    # Save the data to the database
                    logger.info("Saving to database...")
                    instance = self.model(
                        source="edgar_form4",
                        url=href,
                        ticker=ticker,
                        date=date,
                        content=content
                    )
                    
                    instance.save()
                    logger.info(f"Successfully saved 10-K data for {ticker}")
                    
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Error processing row: {str(e)}")
                    logger.error(f"Error details: {type(e).__name__}")
                    continue

        logger.info("Finished 10-K data extraction")
        time.sleep(10)  # Wait longer to see the result

    def extract_content_from_html(self, soup):
        full_content = ""
        seen_texts = set()

        for tag in soup.find_all(['div', 'span', 'table']):
            if tag.name == 'table':
                table_md = self.convert_table_to_markdown(tag)
                full_content += f"\n=== Table ===\n{table_md}\n"
            elif tag.name in ['div', 'span']:
                # Only process direct text, not nested
                if tag.find(['div', 'span', 'table']):
                    continue  # Skip if this tag contains nested tags

                text = tag.get_text(strip=True)
                if not text or text in seen_texts:
                    continue
                seen_texts.add(text)

                style = tag.get('style', '').lower()
                is_section_header = (
                    re.search(r'item\s+\d+[a-z]?[.:]?', text.lower()) and
                    ("700" in style or "bold" in style)
                )

                # Optionally skip boilerplate
                if text.lower().replace(" ", "") in ["tableofcontents", "partii"]:
                    continue

                if is_section_header:
                    full_content += f"\n=== Section: {text} ===\n"
                else:
                    full_content += text + "\n"

        return full_content.strip()


    def convert_table_to_markdown(self, table_tag, caption=None):
        """
        Converts an HTML <table> BeautifulSoup tag to LLM-friendly Markdown.
        - Flattens colspans/rowspans
        - Ensures a header row (synthesizes if missing)
        - Fills empty headers with 'Column N'
        - Optionally adds a caption
        """
        def get_cell_text(cell):
            # Extracts all text, including from nested tags
            return ' '.join(cell.stripped_strings).replace('\n', ' ').strip()

        grid = []
        rowspans = {}

        for row in table_tag.find_all("tr"):
            cells = []
            col_idx = 0
            for cell in row.find_all(['td', 'th']):
                # Fill in cells extended from previous row
                while rowspans.get(col_idx, 0):
                    cells.append(rowspans[col_idx][0])
                    rowspans[col_idx][1] -= 1
                    if rowspans[col_idx][1] == 0:
                        del rowspans[col_idx]
                    col_idx += 1

                text = get_cell_text(cell)
                colspan = int(cell.get('colspan', 1))
                rowspan = int(cell.get('rowspan', 1))

                for i in range(colspan):
                    cells.append(text)
                    if rowspan > 1:
                        rowspans[col_idx] = [text, rowspan - 1]
                    col_idx += 1
            # Fill in any remaining rowspans at the end of the row
            while rowspans.get(col_idx, 0):
                cells.append(rowspans[col_idx][0])
                rowspans[col_idx][1] -= 1
                if rowspans[col_idx][1] == 0:
                    del rowspans[col_idx]
                col_idx += 1
            grid.append(cells)

        # Normalize all rows to the same length
        max_cols = max(len(row) for row in grid)
        for row in grid:
            row += [''] * (max_cols - len(row))

        # Ensure header row exists and is non-empty
        header = grid[0]
        for i, h in enumerate(header):
            if not h.strip():
                header[i] = f"Column {i+1}"
        grid[0] = header

        # Optionally add a caption
        md = ""
        if caption:
            md += f"**Table: {caption}**\n\n"

        # Build Markdown
        md += "| " + " | ".join(header) + " |\n"
        md += "| " + " | ".join(["---"] * max_cols) + " |\n"
        for row in grid[1:]:
            md += "| " + " | ".join(row) + " |\n"
        return md.strip()
