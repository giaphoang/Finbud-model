from core import get_logger
from models.base import DataModel
from models.raw import (
    EdgarFillingRawModel,
    EarningsCallTranscriptRawModel,
    InvestopediaTermsRawModel,
    MacroEconomicReportRawModel
)

from data_logic.chunking_data_handlers import (
    ChunkingDataHandler,
    EdgarFillingChunkingHandler,
    EarningsCallTranscriptChunkingHandler,
    InvestopediaTermsChunkingHandler,
    MacroEconomicReportChunkingHandler,
    InvestopediaPersonalFinanceChunkingHandler,
    YahooChunkingHandler
)

from data_logic.cleaning_data_handlers import (
    CleaningDataHandler,
    EdgarFillingCleaningHandler,
    EarningsCallTranscriptCleaningHandler,
    InvestopediaTermsCleaningHandler,
    YahooCleaningHandler,
    MacroEconomicReportCleaningHandler,
    InvestopediaPersonalFinanceCleaningHandler
)

from data_logic.embedding_data_handlers import (
    EmbeddingDataHandler,
    EdgarFillingEmbeddingHandler,
    EarningsCallTranscriptEmbeddingHandler,
    InvestopediaTermsEmbeddingHandler,
    MacroEconomicReportEmbeddingHandler
)

logger = get_logger(__name__)


class RawDispatcher:
    @staticmethod
    def handle_mq_message(message: dict) -> DataModel:
        data_type = message.get("type")

        logger.info("Received message.", data_type=data_type)

        if data_type == "edgar_fillings":
            return EdgarFillingRawModel(**message)
        elif data_type == "earnings_call_transcript":
            return EarningsCallTranscriptRawModel(**message)
        elif data_type == "yahoo":
            return YahooFinanceRawModel(**message)
        elif data_type == "bloomberg":
            return BloombergRawModel(**message)
        elif data_type == "investopedia_personal_finance":
            return InvestopediaPersonalFinanceRawModel(**message)
        elif data_type == "investopedia_terms":
            return InvestopediaTermsRawModel(**message)
        elif data_type == "macro_economic_reports":
            return MacroEconomicReportRawModel(**message)
        else:
            raise ValueError("Unsupported data type")


class CleaningHandlerFactory:
    @staticmethod
    def create_handler(data_type) -> CleaningDataHandler:
        if data_type == "edgar_fillings":
            return EdgarFillingCleaningHandler()
        elif data_type == "earnings_call_transcript":
            return EarningsCallTranscriptCleaningHandler()
        elif data_type == "investopedia_terms":
            return InvestopediaTermsCleaningHandler()
        elif data_type == "macro_economic_reports":
            return MacroEconomicReportCleaningHandler()
        else:
            raise ValueError("Unsupported data type")


class CleaningDispatcher:
    cleaning_factory = CleaningHandlerFactory()

    @classmethod
    def dispatch_cleaner(cls, data_model: DataModel) -> DataModel:
        data_type = data_model.type
        handler = cls.cleaning_factory.create_handler(data_type)
        clean_model = handler.clean(data_model)

        logger.info(
            "Data cleaned successfully.",
            data_type=data_type,
            cleaned_content_len=len(clean_model.cleaned_content),
        )

        return clean_model


class ChunkingHandlerFactory:
    @staticmethod
    def create_handler(data_type) -> ChunkingDataHandler:
        if data_type == "edgar_fillings":
            return EdgarFillingChunkingHandler()
        elif data_type == "earnings_call_transcript":
            return EarningsCallTranscriptChunkingHandler()
        elif data_type == "investopedia_terms":
            return InvestopediaTermsChunkingHandler()
        elif data_type == "macro_economic_reports":
            return MacroEconomicReportChunkingHandler()
        else:
            raise ValueError("Unsupported data type")


class ChunkingDispatcher:
    chunking_factory = ChunkingHandlerFactory()

    @classmethod
    def dispatch_chunker(cls, data_model: DataModel) -> list[DataModel]:
        data_type = data_model.type
        handler = cls.chunking_factory.create_handler(data_type)
        chunk_models = handler.chunk(data_model)

        logger.info(
            "Cleaned content chunked successfully.",
            num=len(chunk_models),
            data_type=data_type,
        )

        return chunk_models


class EmbeddingHandlerFactory:
    @staticmethod
    def create_handler(data_type) -> EmbeddingDataHandler:
        if data_type == "edgar_fillings":
            return EdgarFillingEmbeddingHandler()
        elif data_type == "earnings_call_transcript":
            return EarningsCallTranscriptEmbeddingHandler()
        elif data_type == "investopedia_terms":
            return InvestopediaTermsEmbeddingHandler()
        elif data_type == "macro_economic_reports":
            return MacroEconomicReportEmbeddingHandler()
        else:
            raise ValueError("Unsupported data type")


class EmbeddingDispatcher:
    embedding_factory = EmbeddingHandlerFactory()

    @classmethod
    def dispatch_embedder(cls, data_model: DataModel) -> DataModel:
        data_type = data_model.type
        handler = cls.embedding_factory.create_handler(data_type)
        embedded_chunk_model = handler.embedd(data_model)

        logger.info(
            "Chunk embedded successfully.",
            data_type=data_type,
            embedding_len=len(embedded_chunk_model.embedded_content),
        )

        return embedded_chunk_model
