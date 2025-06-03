import time
from bs4 import BeautifulSoup
import requests
from aws_lambda_powertools import Logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from crawlers.base import BaseAbstractCrawler
from core.db.documents import YahooFinanceDocument

logger = Logger(service="llm-twin-course/crawler")

class YahooFinanceCrawler(BaseAbstractCrawler):
    """
    Crawls: https://finance.yahoo.com/topic/economic-news/
    Collects: headline, link, summary snippet (if any)
    """

    model = YahooFinanceDocument

    def __init__(self, scroll_limit: int = 3):
        super().__init__(scroll_limit=scroll_limit)

    def extract(self) -> None:
        self.driver.get("https://finance.yahoo.com/topic/economic-news/")
        wait = WebDriverWait(self.driver, 10)
        wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "ul.stream-items li")
            )
        )
        
        articles = self.driver.find_elements(
            By.CSS_SELECTOR,
            "li.story-item"
        )
        
        logger.info(f"Found {len(articles)} Yahoo articles to process")
        
        
        for elem in articles:
            try:
                anchor = elem.find_element(By.CSS_SELECTOR, "a")
                link = anchor.get_attribute("href")
                title = elem.find_element(By.CSS_SELECTOR, "h3.clamp").text.strip()

                summary = ""
                try:
                    summary_elem = elem.find_element(
                        By.CSS_SELECTOR, "p.clamp"
                    )
                    summary = summary_elem.text.strip()
                except:
                    summary = None
                

                doc = YahooFinanceDocument(
                    source="yahoo",
                    title=title,
                    link=link,
                    summary=summary,
                    publish_date=None
                )
                doc.save()
                print(f"[Yahoo] Saved: {title}")
            except Exception as e:
                print("[Yahoo] Skipping one article due to:", e)
                continue

        print("Yahoo Finance crawl complete.")
        time.sleep(2)