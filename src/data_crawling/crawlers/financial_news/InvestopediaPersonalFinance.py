import time
import requests
from typing import Dict, List

from aws_lambda_powertools import Logger
from bs4 import BeautifulSoup
from bs4.element import Tag
from config import settings
from core.errors import ImproperlyConfigured
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from crawlers.base import BaseAbstractCrawler
from core.db.documents import FinancialNewsDocument


class InvestopediaPersonalFinanceCrawler(BaseAbstractCrawler):
    """
    Crawls: https://www.investopedia.com/personal-finance-news-5114159
    Collects: headline, link, summary, published date (if available)
    """
    
    model = FinancialNewsDocument
    logger = Logger(service="llm-twin-course/crawler")

    def __init__(self, scroll_limit: int = 1):
        super().__init__(scroll_limit=scroll_limit)

    def extract(self) -> None:
        self.driver.get("https://www.investopedia.com/personal-finance-news-5114159")
        wait = WebDriverWait(self.driver, 10)

        # Wait for the list of earnings report articles to appear
        wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "#main")
            )
        )

        cards = self.driver.find_elements(
            By.CSS_SELECTOR, "a.comp.mntl-card-list-items.mntl-document-card.mntl-card.card.card--no-image"
        )
        print(len(cards), "cards found on Investopedia Personal Finance page")
        # Collect all links from the cards
        links = []
        for idx, card in enumerate(cards):
            link = card.get_attribute("href")
            if link:
                links.append(link)
            print("Processing card", idx, "with link:", link)
        if not cards:
            raise ImproperlyConfigured(
            "No cards found on the Investopedia Personal Finance page. "
            "Please check the CSS selector or the page structure."
            )
        print("Collected links:", links)

        for idx, link in enumerate(links):
            try:
                print("link:", link)

                summary = None
                if link:  
                    self.driver.get(link)
                    try:
                        # Wait until the page is loaded or the title is visible
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
                        )
                        title = self.driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
                        # Extract the date from the div with class "mntl-attribution__item-date"
                        try:
                            date_elem = self.driver.find_element(By.CSS_SELECTOR, "div.mntl-attribution__item-date")
                            date_text = date_elem.text.strip()
                            # Remove "Published " prefix if present
                            # Extract the date after the first space character
                            from dateutil.parser import parse as dateparse
                            first_space = date_text.find(" ")
                            if first_space != -1:
                                date = date_text[first_space + 1:].strip()
                        except Exception as date_exc:
                            date = None
                            print(f"[Investopedia Personal Finance] Failed to extract date for card {idx} - {title}: {date_exc}")
                        takeaway = self.driver.find_elements(
                            By.CSS_SELECTOR, "div .mntl-sc-block-universal-callout__body li"
                        )
                        takeaway_str = [point.text.strip() for point in takeaway]
                        summary = ' '.join(takeaway_str)
                    except Exception as summary_exc: 
                        summary = None
                        print(f"[Investopedia Personal Finance] Failed to extract summary for card {idx} - {title}: {summary_exc}")

                doc = self.model(
                    source="investopedia_personal_finance",
                    title=title,
                    link=link,
                    summary=summary,
                    date=date
                )
                doc.save()
                print(f"[Investopedia Personal Finance] Saved: {title}")
            except Exception as e:
                print(f"[Investopedia Personal Finance] Skipping card {idx}. Exception: {e}")
                try:
                    # Try to log card info if possible
                    title = card.text if card else 'N/A'
                    print(f"[Investopedia Personal Finance] Card {idx} text: {title}")
                except Exception as inner_exc:
                    print(f"[Investopedia Personal Finance] Could not get card text for card {idx}: {inner_exc}")
                break

        print("Investopedia Personal Finance crawl complete.")
        time.sleep(2)
