import hashlib
from abc import ABC, abstractmethod
from typing import List, Any

from models.base import DataModel
from models.chunk import EdgarFillingChunkModel, EarningsCallTranscriptChunkModel, YahooFinanceChunkModel, BloombergChunkModel, InvestopediaPersonalFinanceChunkModel, InvestopediaTermsChunkModel, MacroEconomicReportChunkModel
from models.clean import EdgarFillingCleanedModel, EarningsCallTranscriptCleanedModel, YahooFinanceCleanedModel, BloombergCleanedModel, InvestopediaPersonalFinanceCleanedModel, InvestopediaTermsCleanedModel, MacroEconomicReportCleanedModel
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


class YahooFinanceChunkingHandler(ChunkingDataHandler):
    def chunk(self, data_model: YahooFinanceCleanedModel) -> List[YahooFinanceChunkModel]:
        data_models_list = []
        
        text_content = data_model.cleaned_content
        chunks = chunk_text(text_content)
        
        for chunk in chunks:
            model = YahooFinanceChunkModel(
                entry_id=data_model.entry_id,
                source=data_model.source,
                title=data_model.title,
                link=data_model.link,
                chunk_id=hashlib.md5(chunk.encode()).hexdigest(),
                chunk_content=chunk,
                publish_date=data_model.publish_date,
                type=data_model.type
            )
            data_models_list.append(model)
        
        return data_models_list

class BloombergChunkingHandler(ChunkingDataHandler):
    def chunk(self, data_model: BloombergCleanedModel) -> List[BloombergChunkModel]:
        data_models_list = []
        
        text_content = data_model.cleaned_content
        chunks = chunk_text(text_content)
        
        for chunk in chunks:
            model = BloombergChunkModel(
                entry_id=data_model.entry_id,
                source=data_model.source,
                title=data_model.title,
                link=data_model.link,
                chunk_id=hashlib.md5(chunk.encode()).hexdigest(),
                chunk_content=chunk,
                publish_date=data_model.publish_date,
                type=data_model.type
            )
            data_models_list.append(model)
            
        return data_models_list

class InvestopediaPersonalFinanceChunkingHandler(ChunkingDataHandler):
    def chunk(self, data_model: InvestopediaPersonalFinanceCleanedModel) -> List[InvestopediaPersonalFinanceChunkModel]:
        data_models_list = []
        
        text_content = data_model.cleaned_content
        chunks = chunk_text(text_content)
        
        for chunk in chunks:
            model = InvestopediaPersonalFinanceChunkModel(
                entry_id=data_model.entry_id,
                source=data_model.source,
                title=data_model.title,
                link=data_model.link,
                chunk_id=hashlib.md5(chunk.encode()).hexdigest(),
                chunk_content=chunk,
                publish_date=data_model.publish_date,
                type=data_model.type
            )
            data_models_list.append(model)
            
        return data_models_list

class InvestopediaTermsChunkingHandler(ChunkingDataHandler):
    def chunk(self, data_model: InvestopediaTermsCleanedModel) -> List[InvestopediaTermsChunkModel]:
        data_models_list = []
        
        text_content = data_model.definition
        chunks = chunk_text(text_content)
        
        for chunk in chunks:
            model = InvestopediaTermsChunkModel(
                entry_id=data_model.entry_id,
                term=data_model.term,
                url=data_model.url,
                chunk_id=hashlib.md5(chunk.encode()).hexdigest(),
                chunk_content=chunk,
                metadata=data_model.metadata,
                crawled_at=data_model.crawled_at,
                type=data_model.type
            )
            data_models_list.append(model)
            
        return data_models_list

class MacroEconomicReportChunkingHandler(ChunkingDataHandler):
    def chunk(self, data_model: MacroEconomicReportCleanedModel) -> List[MacroEconomicReportChunkModel]:
        data_models_list = []
        chunks = []
        
        for section in data_model.content.sections:
            if section.text:
                chunks.extend(chunk_text(section.text))
            if section.list:
                chunks.extend(section.list)
        
        for chunk in chunks:
            model = MacroEconomicReportChunkModel(
                entry_id=data_model.entry_id,
                date=data_model.date,
                chunk_id=hashlib.md5(chunk.encode()).hexdigest(),
                chunk_content=chunk,
                metadata=data_model.metadata,
                crawled_at=data_model.crawled_at,
                type=data_model.type
            )
            data_models_list.append(model)
            
        return data_models_list
