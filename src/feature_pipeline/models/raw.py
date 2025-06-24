from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from models.base import DataModel

class EdgarFillingRawModel(DataModel):
    id: str = Field(alias="entry_id")
    source: str
    url: str
    date: str
    ticker: str
    content: str


class EarningsCallTranscriptRawModel(DataModel):
    id: str = Field(alias="entry_id")
    source: str
    url: str
    date: str
    content: str


class FinancialNewsRawModel(DataModel):
    id: str = Field(alias="entry_id")
    source: str
    title: str
    link: Optional[str]
    summary: Optional[str]
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


class InvestopediaTermsRawModel(DataModel):
    id: str = Field(alias="entry_id")
    term: str
    url: str
    definition: str
    content: Content
    crawled_at: datetime = Field(default_factory=datetime.utcnow)


class MacroEconomicReportRawModel(DataModel):
    id: str = Field(alias="entry_id")
    date: datetime
    type: str
    content: Content
    crawled_at: datetime = Field(default_factory=datetime.utcnow)
    content: dict
    author_id: str | None = None
    image: Optional[str] = None

class YahooRawModel(DataModel):
    platform: str
    link: str
    content: dict
    author_id: str


class BloombergRawModel(DataModel):
    platform: str
    link: str
    content: dict
    author_id: str


class InvestopediaPersonalFinanceRawModel(DataModel):
    platform: str
    link: str
    content: dict
    author_id: str
