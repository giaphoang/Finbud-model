# src/data_crawling/crawlers/Bloomberg.py
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from crawlers.base import BaseAbstractCrawler
from core.db.documents import BloombergDocument


class BloombergCrawler(BaseAbstractCrawler):
    """
    Crawls: https://www.bloomberg.com/markets
    Collects: headline, link
    """

    model = BloombergDocument

    def __init__(self, scroll_limit: int = 2):
        super().__init__(scroll_limit=scroll_limit)

    def extract(self) -> None:
        self.driver.get("https://www.bloomberg.com/markets")
        wait = WebDriverWait(self.driver, 10)

        wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, ".gridLayout_gridLayout__zTmc7")
            )
        )

        articles = self.driver.find_elements(
            By.CSS_SELECTOR, "a.StoryBlock_storyLink__5nXw8"
        )

        for elem in articles:
            try:
                title_elem = elem.find_element(By.CSS_SELECTOR, "span")
                title = title_elem.text.strip()

                # anchor = elem.find_element(By.CSS_SELECTOR, "a")
                link = elem.get_attribute("href")

            

                doc = BloombergDocument(
                    source="bloomberg",
                    title=title,
                    link=link,
                    summary=None,
                    publish_date=None
                )
                doc.save()
                print(f"[Bloomberg] Saved: {title}")
            except Exception as e:
                print("[Bloomberg] Skipping one article due to:", e)
                continue

        print("Bloomberg crawl complete.")
        time.sleep(2)
