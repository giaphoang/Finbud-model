from typing import Any

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from core import lib
from crawlers import _10KCrawler, _10QCrawler, DEF14ACrawler, Form4Crawler, _8KCrawler, EarningsCallTranscriptCrawler, YahooFinanceCrawler, InvestopediaPersonalFinanceCrawler, FOMCEconomicCrawler, BEIGEconomicCrawler, InvestopediaTermsCrawler

from dispatcher import CrawlerDispatcher

logger = Logger(service="llm-twin-course/crawler")

_dispatcher = CrawlerDispatcher()
_dispatcher.register("8k", _8KCrawler)
_dispatcher.register("10k", _10KCrawler)
_dispatcher.register("10q", _10QCrawler)
_dispatcher.register("def14a", DEF14ACrawler)
_dispatcher.register("form4", Form4Crawler)

_dispatcher.register("yahoo", YahooFinanceCrawler)
_dispatcher.register("investopedia_personal_finance", InvestopediaPersonalFinanceCrawler)
_dispatcher.register("earnings_call_transcript", EarningsCallTranscriptCrawler)
_dispatcher.register("fomc_economic", FOMCEconomicCrawler)
_dispatcher.register("beige_economic", BEIGEconomicCrawler)
_dispatcher.register("investopedia_terms", InvestopediaTermsCrawler)



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
        "link": "earnings_call_transcript",  # This will trigger the crawler
    }
    handler(event, None)
