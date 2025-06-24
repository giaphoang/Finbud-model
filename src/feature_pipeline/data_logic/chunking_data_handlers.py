import hashlib
from abc import ABC, abstractmethod
from typing import List, Any

from models.base import DataModel

from models.chunk import EdgarFillingChunkModel, EarningsCallTranscriptChunkModel, FinancialNewsChunkModel, YahooChunkModel, InvestopediaTermsChunkModel, MacroEconomicReportChunkModel, InvestopediaPersonalFinanceChunkModel
from models.clean import EdgarFillingCleanedModel, EarningsCallTranscriptCleanedModel, FinancialNewsCleanedModel, YahooCleanedModel, InvestopediaTermsCleanedModel, MacroEconomicReportCleanedModel, InvestopediaPersonalFinanceCleanedModel

from utils.chunking import chunk_text


class ChunkingDataHandler(ABC):
    """
    Abstract class for all Chunking data handlers.
    All data transformations logic for the chunking step is done here
    """

    @abstractmethod
    def chunk(self, data_model: DataModel) -> list[DataModel]:
        pass

class EdgarFillingChunkingHandler(ChunkingDataHandler):
    def chunk(self, data_model: EdgarFillingCleanedModel) -> list[EdgarFillingChunkModel]:
        data_models_list = []
        
        text_content = data_model.cleaned_content
        chunks = chunk_text(text_content)
        
        for chunk in chunks:
            model = EdgarFillingChunkModel(
                entry_id=data_model.entry_id,
                source=data_model.source,
                url=data_model.url,
                date=data_model.date,
                ticker=data_model.ticker,
                chunk_id=hashlib.md5(chunk.encode()).hexdigest(),
                chunk_content=chunk,
                type=data_model.type,
            )
            data_models_list.append(model)
        
        return data_models_list
    
class EarningsCallTranscriptChunkingHandler(ChunkingDataHandler):
    def chunk(self, data_model: EarningsCallTranscriptCleanedModel) -> list[EarningsCallTranscriptChunkModel]:
        data_models_list = []
        
        text_content = data_model.cleaned_content
        chunks = chunk_text(text_content)
        
        for chunk in chunks:
            model = EarningsCallTranscriptChunkModel(
                entry_id=data_model.entry_id,
                source=data_model.source,
                url=data_model.url,
                date=data_model.date,
                chunk_id=hashlib.md5(chunk.encode()).hexdigest(),
                chunk_content=chunk,
                type=data_model.type,
            )
            data_models_list.append(model)
        
        return data_models_list


class FinancialNewsChunkingHandler(ChunkingDataHandler):
    def chunk(self, data_model: FinancialNewsCleanedModel) -> List[FinancialNewsChunkModel]:
        data_models_list = []
        
        text_content = data_model.cleaned_content
        chunks = chunk_text(text_content)
        
        for chunk in chunks:
            model = FinancialNewsChunkModel(
                entry_id=data_model.entry_id,
                source=data_model.source,
                title=data_model.title,
                link=data_model.link,
                chunk_id=hashlib.md5(chunk.encode()).hexdigest(),
                chunk_content=chunk,
                date=data_model.date,
                type=data_model.type
            )
            data_models_list.append(model)
            
        return data_models_list

class InvestopediaTermsChunkingHandler(ChunkingDataHandler):
    def chunk(self, data_model: InvestopediaTermsCleanedModel) -> List[InvestopediaTermsChunkModel]:
        data_models_list = []
        
        text_content = data_model.cleaned_content
        chunks = chunk_text(text_content)
        
        for chunk in chunks:
            model = InvestopediaTermsChunkModel(
                entry_id=data_model.entry_id,
                term=data_model.term,
                url=data_model.url,
                definition=data_model.definition,
                chunk_id=hashlib.md5(chunk.encode()).hexdigest(),
                chunk_content=chunk,
                crawled_at=data_model.crawled_at,
                type=data_model.type
            )
            data_models_list.append(model)
            
        return data_models_list

class MacroEconomicReportChunkingHandler(ChunkingDataHandler):
    def chunk(self, data_model: MacroEconomicReportCleanedModel) -> List[MacroEconomicReportChunkModel]:
        data_models_list = []
        
        # Use cleaned_content directly since it's already flattened
        chunks = chunk_text(data_model.cleaned_content)
        
        for chunk in chunks:
            model = MacroEconomicReportChunkModel(
                entry_id=data_model.entry_id,
                date=data_model.date,
                chunk_id=hashlib.md5(chunk.encode()).hexdigest(),
                chunk_content=chunk,
                crawled_at=data_model.crawled_at,
                type=data_model.type
            )
            data_models_list.append(model)
            
        return data_models_list


class YahooChunkingHandler(ChunkingDataHandler):
    def chunk(self, data_model: YahooCleanedModel) -> list[YahooChunkModel]:
        data_models_list = []

        text_content = data_model.cleaned_content
        chunks = chunk_text(text_content)

        for chunk in chunks:
            model = YahooChunkModel(
                entry_id=data_model.entry_id,
                platform=data_model.platform,
                link=data_model.link,
                chunk_id=hashlib.md5(chunk.encode()).hexdigest(),
                chunk_content=chunk,
                author_id=data_model.author_id,
                type=data_model.type,
            )
            data_models_list.append(model)

        return data_models_list

class BloombergChunkingHandler(ChunkingDataHandler):
    def chunk(self, data_model: BloombergCleanedModel) -> list[BloombergChunkModel]:
        data_models_list = []

        text_content = data_model.cleaned_content
        chunks = chunk_text(text_content)

        for chunk in chunks:
            model = BloombergChunkModel(
                entry_id=data_model.entry_id,
                platform=data_model.platform,
                link=data_model.link,
                chunk_id=hashlib.md5(chunk.encode()).hexdigest(),
                chunk_content=chunk,
                author_id=data_model.author_id,
                type=data_model.type,
            )
            data_models_list.append(model)

        return data_models_list

class InvestopediaPersonalFinanceChunkingHandler(ChunkingDataHandler):
    def chunk(self, data_model: InvestopediaPersonalFinanceCleanedModel) -> list[InvestopediaPersonalFinanceChunkModel]:
        data_models_list = []
        
        text_content = data_model.cleaned_content
        chunks = chunk_text(text_content)

        for chunk in chunks:
            model = InvestopediaPersonalFinanceChunkModel(
                entry_id=data_model.entry_id,
                platform=data_model.platform,
                link=data_model.link,
                chunk_id=hashlib.md5(chunk.encode()).hexdigest(),
                chunk_content=chunk,
                author_id=data_model.author_id,
                type=data_model.type,
            )
            data_models_list.append(model)

        return data_models_list