from typing import Tuple, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

import numpy as np

from models.base import VectorDBDataModel

class EdgarFillingEmbeddedChunkModel(VectorDBDataModel):
    entry_id: str
    source: str
    url: str
    date: str
    ticker: str
    chunk_id: str
    chunk_content: str
    embedded_content: np.ndarray
    type: str

    class Config:
        arbitrary_types_allowed = True

    def to_payload(self) -> Tuple[str, np.ndarray, dict]:
        data = {
            "id": self.entry_id,
            "source": self.source,
            "url": self.url,
            "date": self.date,
            "ticker": self.ticker,
            "content": self.chunk_content,
            "type": self.type,
        }

        return self.chunk_id, self.embedded_content, data


class EarningsCallTranscriptEmbeddedChunkModel(VectorDBDataModel):
    entry_id: str
    source: str
    url: str
    date: str
    chunk_id: str
    chunk_content: str
    embedded_content: np.ndarray
    type: str

    class Config:
        arbitrary_types_allowed = True

    def to_payload(self) -> Tuple[str, np.ndarray, dict]:
        data = {
            "id": self.entry_id,
            "source": self.source,
            "url": self.url,
            "date": self.date,
            "content": self.chunk_content,
            "type": self.type,
        }

        return self.chunk_id, self.embedded_content, data

class YahooFinanceEmbeddedChunkModel(VectorDBDataModel):
    entry_id: str
    source: str
    title: str
    link: Optional[str]
    chunk_id: str
    chunk_content: str
    embedded_content: np.ndarray
    publish_date: Optional[str]
    type: str
    
    class Config:
        arbitrary_types_allowed = True

    def to_payload(self) -> Tuple[str, List[float], dict]:
        data = {
            "id": self.entry_id,
            "type": self.type,
            "source": self.source,
            "title": self.title,
            "link": self.link,
            "content": self.chunk_content,
            "publish_date": self.publish_date
        }
        return self.chunk_id, self.embedded_content, data


class BloombergEmbeddedChunkModel(VectorDBDataModel):
    entry_id: str
    source: str
    title: str
    link: Optional[str]
    chunk_id: str
    chunk_content: str
    embedded_content: np.ndarray
    publish_date: Optional[str]
    type: str
    
    class Config:
        arbitrary_types_allowed = True

    def to_payload(self) -> Tuple[str, List[float], dict]:
        data = {
            "id": self.entry_id,
            "type": self.type,
            "source": self.source,
            "title": self.title,
            "link": self.link,
            "content": self.chunk_content,
            "publish_date": self.publish_date
        }
        return self.chunk_id, self.embedded_content, data


class InvestopediaPersonalFinanceEmbeddedChunkModel(VectorDBDataModel):
    entry_id: str
    source: str
    title: str
    link: Optional[str]
    chunk_id: str
    chunk_content: str
    embedded_content: np.ndarray
    publish_date: Optional[datetime]
    type: str
    
    class Config:
        arbitrary_types_allowed = True

    def to_payload(self) -> Tuple[str, List[float], dict]:
        data = {
            "id": self.entry_id,
            "type": self.type,
            "source": self.source,
            "title": self.title,
            "link": self.link,
            "content": self.chunk_content,
            "publish_date": self.publish_date
        }
        return self.chunk_id, self.embedded_content, data


class Section(BaseModel):
    heading: str
    text: Optional[str] = None
    list: Optional[List[str]] = None


class Content(BaseModel):
    title: str
    sections: List[Section]


class Metadata(BaseModel):
    source: str
    author: Optional[str] = None
    last_updated: Optional[str] = None
    platform: str
    tags: Optional[List[str]] = None


class InvestopediaTermsEmbeddedChunkModel(VectorDBDataModel):
    entry_id: str
    term: str
    url: str
    chunk_id: str
    chunk_content: str
    embedded_content: np.ndarray
    metadata: Metadata
    crawled_at: datetime
    type: str
    
    class Config:
        arbitrary_types_allowed = True

    def to_payload(self) -> Tuple[str, List[float], dict]:
        data = {
            "id": self.entry_id,
            "type": self.type,
            "term": self.term,
            "url": self.url,
            "content": self.chunk_content,
            "metadata": self.metadata.dict(),
            "crawled_at": self.crawled_at
        }
        return self.chunk_id, self.embedded_content, data


class MacroEconomicReportEmbeddedChunkModel(VectorDBDataModel):
    entry_id: str
    date: datetime
    chunk_id: str
    chunk_content: str
    embedded_content: np.ndarray
    metadata: Metadata
    crawled_at: datetime
    type: str
    
    class Config:
        arbitrary_types_allowed = True

    def to_payload(self) -> Tuple[str, List[float], dict]:
        data = {
            "id": self.entry_id,
            "type": self.type,
            "date": self.date,
            "content": self.chunk_content,
            "metadata": self.metadata.dict(),
            "crawled_at": self.crawled_at
        }
        return self.chunk_id, self.embedded_content, data
