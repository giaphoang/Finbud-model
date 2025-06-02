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
from core.db.documents import InvestopediaDocument


class InvestopediaCrawler(BaseAbstractCrawler):
    """
    Crawls: https://www.investopedia.com/earnings-reports-5218419
    Collects: headline, link, published date (if available)
    """
    
    model = InvestopediaDocument

    def __init__(self, scroll_limit: int = 1):
        super().__init__(scroll_limit=scroll_limit)

    def extract(self) -> None:
        self.driver.get("https://www.investopedia.com/earnings-reports-5218419")
        wait = WebDriverWait(self.driver, 10)

        # Wait for the list of earnings report articles to appear
        wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "#main")
            )
        )

        cards = self.driver.find_elements(
            By.CSS_SELECTOR, "a[id^=mntl-card-list-items_]"
        )

        for card in cards:
            try:
                title_elem = card.find_element(
                    By.CSS_SELECTOR, ".card__title-text"
                )
                # anchor = title_elem.find_element(By.TAG_NAME, "a")
                title = title_elem.text.strip()
                link = card.get_attribute("href")

                pub_date = None
                try:
                    time_elem = card.find_element(By.CSS_SELECTOR, ".displayed-date__date")
                    date_text = time_elem.get_attribute("datetime") or time_elem.text
                    from dateutil.parser import parse as dateparse
                    pub_date = dateparse(date_text)
                except:
                    pub_date = None

                doc = InvestopediaDocument(
                    source="investopedia",
                    title=title,
                    link=link,
                    summary=None,
                    publish_date=pub_date
                )
                doc.save()
                print(f"[Investopedia] Saved: {title}")
            except Exception as e:
                print("[Investopedia] Skipping one card due to:", e)
                continue

        print("Investopedia crawl complete.")
        time.sleep(2)
