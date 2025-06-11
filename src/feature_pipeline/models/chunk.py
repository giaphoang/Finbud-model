from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from models.base import DataModel

class EdgarFillingChunkModel(DataModel):
    entry_id: str
    source: str
    url: str
    date: str
    ticker: str
    chunk_id: str
    chunk_content: str


class EarningsCallTranscriptChunkModel(DataModel):
    entry_id: str
    source: str
    url: str
    date: str
    chunk_id: str
    chunk_content: str


class FinancialNewsChunkModel(DataModel):
    entry_id: str
    source: str
    title: str
    link: Optional[str]
    chunk_id: str
    chunk_content: str
    date: Optional[str]

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


class InvestopediaTermsChunkModel(DataModel):
    entry_id: str
    term: str
    url: str
    definition: str
    chunk_id: str
    chunk_content: str
    crawled_at: datetime = Field(default_factory=datetime.utcnow)


class MacroEconomicReportChunkModel(DataModel):
    entry_id: str
    date: datetime
    chunk_id: str
    chunk_content: str
    crawled_at: datetime = Field(default_factory=datetime.utcnow)
