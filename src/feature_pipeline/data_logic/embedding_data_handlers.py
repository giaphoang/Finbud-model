from abc import ABC, abstractmethod
from typing import Any
from models.base import DataModel
from models.chunk import (
    EdgarFillingChunkModel,
    EarningsCallTranscriptChunkModel,
    YahooFinanceChunkModel,
    BloombergChunkModel,
    InvestopediaPersonalFinanceChunkModel,
    InvestopediaTermsChunkModel,
    MacroEconomicReportChunkModel
)
from models.embedded_chunk import (
    EdgarFillingEmbeddedChunkModel,
    EarningsCallTranscriptEmbeddedChunkModel,
    YahooFinanceEmbeddedChunkModel,
    BloombergEmbeddedChunkModel,
    InvestopediaPersonalFinanceEmbeddedChunkModel,
    InvestopediaTermsEmbeddedChunkModel,
    MacroEconomicReportEmbeddedChunkModel
)
from utils.embeddings import embedd_text

class EmbeddingDataHandler(ABC):
    """
    Abstract class for all embedding data handlers.
    All data transformations logic for the embedding step is done here
    """

    @abstractmethod
    def embedd(self, data_model: DataModel) -> DataModel:
        pass

class EdgarFillingEmbeddingHandler(EmbeddingDataHandler):
    def embedd(self, data_model: EdgarFillingChunkModel) -> EdgarFillingEmbeddedChunkModel:
        return EdgarFillingEmbeddedChunkModel(
            entry_id=data_model.entry_id,
            type=data_model.type,
            source=data_model.source,
            url=data_model.url,
            date=data_model.date,
            ticker=data_model.ticker,
            chunk_id=data_model.chunk_id,
            chunk_content=data_model.chunk_content,
            embedded_content=embedd_text(data_model.chunk_content)
        )

class EarningsCallTranscriptEmbeddingHandler(EmbeddingDataHandler):
    def embedd(self, data_model: EarningsCallTranscriptChunkModel) -> EarningsCallTranscriptEmbeddedChunkModel:
        return EarningsCallTranscriptEmbeddedChunkModel(
            entry_id=data_model.entry_id,
            type=data_model.type,
            source=data_model.source,
            url=data_model.url,
            date=data_model.date,
            chunk_id=data_model.chunk_id,
            chunk_content=data_model.chunk_content,
            embedded_content=embedd_text(data_model.chunk_content)
        )

class YahooFinanceEmbeddingHandler(EmbeddingDataHandler):
    def embedd(self, data_model: YahooFinanceChunkModel) -> YahooFinanceEmbeddedChunkModel:
        return YahooFinanceEmbeddedChunkModel(
            entry_id=data_model.entry_id,
            type=data_model.type,
            source=data_model.source,
            title=data_model.title,
            link=data_model.link,
            publish_date=data_model.publish_date,
            chunk_id=data_model.chunk_id,
            chunk_content=data_model.chunk_content,
            embedded_content=embedd_text(data_model.chunk_content)
        )

class BloombergEmbeddingHandler(EmbeddingDataHandler):
    def embedd(self, data_model: BloombergChunkModel) -> BloombergEmbeddedChunkModel:

        return BloombergEmbeddedChunkModel(
            entry_id=data_model.entry_id,
            type=data_model.type,
            source=data_model.source,
            title=data_model.title,
            link=data_model.link,
            publish_date=data_model.publish_date,
            chunk_id=data_model.chunk_id,
            chunk_content=data_model.chunk_content,
            embedded_content=embedd_text(data_model.chunk_content)
        )

class InvestopediaPersonalFinanceEmbeddingHandler(EmbeddingDataHandler):
    def embedd(self, data_model: InvestopediaPersonalFinanceChunkModel) -> InvestopediaPersonalFinanceEmbeddedChunkModel:
        return InvestopediaPersonalFinanceEmbeddedChunkModel(
            entry_id=data_model.entry_id,
            type=data_model.type,
            source=data_model.source,
            title=data_model.title,
            link=data_model.link,
            chunk_id=data_model.chunk_id,
            chunk_content=data_model.chunk_content,
            embedded_content=embedd_text(data_model.chunk_content)
        )

class InvestopediaTermsEmbeddingHandler(EmbeddingDataHandler):
    def embedd(self, data_model: InvestopediaTermsChunkModel) -> InvestopediaTermsEmbeddedChunkModel:
        return InvestopediaTermsEmbeddedChunkModel(
            entry_id=data_model.entry_id,
            type=data_model.type,
            term=data_model.term,
            url=data_model.url,
            metadata=data_model.metadata,
            crawled_at=data_model.crawled_at,
            chunk_id=data_model.chunk_id,
            chunk_content=data_model.chunk_content,
            embedded_content=embedd_text(data_model.chunk_content)
        )

class MacroEconomicReportEmbeddingHandler(EmbeddingDataHandler):
    def embedd(self, data_model: MacroEconomicReportChunkModel) -> MacroEconomicReportEmbeddedChunkModel:
        return MacroEconomicReportEmbeddedChunkModel(
            entry_id=data_model.entry_id,
            type=data_model.type,
            date=data_model.date,
            chunk_id=data_model.chunk_id,
            chunk_content=data_model.chunk_content,
            metadata=data_model.metadata,
            crawled_at=data_model.crawled_at,
            embedded_content=embedd_text(data_model.chunk_content)
        )
