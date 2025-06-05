from abc import ABC, abstractmethod
from typing import Any
from models.base import DataModel
from models.clean import EdgarFillingCleanedModel, EarningsCallTranscriptCleanedModel, YahooFinanceCleanedModel, BloombergCleanedModel, InvestopediaPersonalFinanceCleanedModel, InvestopediaTermsCleanedModel, MacroEconomicReportCleanedModel
from models.raw import EdgarFillingRawModel, EarningsCallTranscriptRawModel, YahooFinanceRawModel, BloombergRawModel, InvestopediaPersonalFinanceRawModel, InvestopediaTermsRawModel, MacroEconomicReportRawModel
from utils.cleaning import clean_text


class CleaningDataHandler(ABC):
    """
    Abstract class for all cleaning data handlers.
    All data transformations logic for the cleaning step is done here
    """

    @abstractmethod
    def clean(self, data_model: DataModel) -> DataModel:
        pass

class EdgarFillingCleaningHandler(CleaningDataHandler):
    def clean(self, raw_data: EdgarFillingRawModel) -> EdgarFillingCleanedModel:
        return EdgarFillingCleanedModel(
            entry_id=raw_data.entry_id,
            type=raw_data.type,
            source=raw_data.source,
            url=raw_data.url,
            date=raw_data.date,
            ticker=raw_data.ticker,
            cleaned_content=clean_text(raw_data.content)
        )

class EarningsCallTranscriptCleaningHandler(CleaningDataHandler):
    def clean(self, raw_data: EarningsCallTranscriptRawModel) -> EarningsCallTranscriptCleanedModel:
        return EarningsCallTranscriptCleanedModel(
            entry_id=raw_data.entry_id,
            type=raw_data.type,
            source=raw_data.source,
            url=raw_data.url,
            date=raw_data.date,
            cleaned_content=clean_text(raw_data.content)
        )

class YahooFinanceCleaningHandler(CleaningDataHandler):
    def clean(self, raw_data: YahooFinanceRawModel) -> YahooFinanceCleanedModel:
        return YahooFinanceCleanedModel(
            entry_id=raw_data.entry_id,
            type=raw_data.type,
            source=raw_data.source,
            title=raw_data.title,
            link=raw_data.link,
            publish_date=raw_data.publish_date,
            cleaned_content=clean_text(raw_data.summary or raw_data.title)
        )

class BloombergCleaningHandler(CleaningDataHandler):
    def clean(self, raw_data: BloombergRawModel) -> BloombergCleanedModel:
        return BloombergCleanedModel(
            entry_id=raw_data.entry_id,
            type=raw_data.type,
            source=raw_data.source,
            title=raw_data.title,
            link=raw_data.link,
            cleaned_content=clean_text(raw_data.summary),
            publish_date=raw_data.publish_date,
        )

class InvestopediaPersonalFinanceCleaningHandler(CleaningDataHandler):
    def clean(self, raw_data: InvestopediaPersonalFinanceRawModel) -> InvestopediaPersonalFinanceCleanedModel:
        return InvestopediaPersonalFinanceCleanedModel(
            entry_id=raw_data.entry_id,
            type=raw_data.type,
            source=raw_data.source,
            title=raw_data.title,
            link=raw_data.link,
            cleaned_content=clean_text(raw_data.summary),
            publish_date=raw_data.publish_date
        )

class InvestopediaTermsCleaningHandler(CleaningDataHandler):
    def clean(self, raw_data: InvestopediaTermsRawModel) -> InvestopediaTermsCleanedModel:
        return InvestopediaTermsCleanedModel(
            entry_id=raw_data.entry_id,
            type=raw_data.type,
            term=raw_data.term,
            url=raw_data.url,
            definition=raw_data.definition,
            cleaned_content=raw_data.content.model_dump(),
            metadata=raw_data.metadata,
            crawled_at=raw_data.crawled_at
        )

class MacroEconomicReportCleaningHandler(CleaningDataHandler):
    def clean(self, raw_data: MacroEconomicReportRawModel) -> MacroEconomicReportCleanedModel:
        return MacroEconomicReportCleanedModel(
            entry_id=raw_data.entry_id,
            type=raw_data.type,
            date=raw_data.date,
            cleaned_content=raw_data.content.model_dump(),
            metadata=raw_data.metadata,
            crawled_at=raw_data.crawled_at
        )
