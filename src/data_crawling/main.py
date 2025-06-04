from typing import Any

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from core import lib
from crawlers import FinancialsCrawler, NewsCrawler, Form4Crawler, ProxyCrawler, YahooFinanceCrawler, BloombergCrawler, InvestopediaCrawler, InvestopediaPersonalFinanceCrawler
from dispatcher import CrawlerDispatcher

logger = Logger(service="llm-twin-course/crawler")

_dispatcher = CrawlerDispatcher()
_dispatcher.register("financials", FinancialsCrawler)
_dispatcher.register("news", NewsCrawler)
_dispatcher.register("form4", Form4Crawler)
_dispatcher.register("proxies", ProxyCrawler)
_dispatcher.register("yahoo", YahooFinanceCrawler)
_dispatcher.register("bloomberg", BloombergCrawler)
_dispatcher.register("investopedia", InvestopediaCrawler)
_dispatcher.register("investopedia_personal_finance", InvestopediaPersonalFinanceCrawler)




def handler(event, context: LambdaContext | None = None) -> dict[str, Any]:
    link = event.get("link")
    crawler = _dispatcher.get_crawler(link)

    try:
        crawler.extract()

        return {"statusCode": 200, "body": "Link processed successfully"}
    except Exception as e:
        return {"statusCode": 500, "body": f"An error occurred: {str(e)}"}


if __name__ == "__main__":
    event = {
        "link": "financials",  # This will trigger the financials crawler
    }
    handler(event, None)
