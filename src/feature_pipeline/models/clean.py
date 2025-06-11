from typing import Optional, Tuple, List
from datetime import datetime
from pydantic import BaseModel, Field

from models.base import VectorDBDataModel

class EdgarFillingCleanedModel(VectorDBDataModel):
    entry_id: str
    source: str
    url: str
    date: str
    ticker: str
    cleaned_content: str
    type: str

    def to_payload(self) -> Tuple[str, dict]:
        data = {
            "source": self.source,
            "url": self.url,
            "date": self.date,
            "ticker": self.ticker,
            "cleaned_content": self.cleaned_content,
            "type": self.type,
        }

        return self.entry_id, data

class EarningsCallTranscriptCleanedModel(VectorDBDataModel):
    entry_id: str
    source: str
    url: str
    date: str
    cleaned_content: str
    type: str
    
    def to_payload(self) -> Tuple[str, dict]:
        data = {
            "source": self.source,
            "url": self.url,
            "date": self.date,
            "cleaned_content": self.cleaned_content,
            "type": self.type,
        }

        return self.entry_id, data

class FinancialNewsCleanedModel(VectorDBDataModel):
    entry_id: str
    source: str
    title: str
    link: Optional[str]
    cleaned_content: Optional[str]
    date: Optional[str]
    type: str

    def to_payload(self) -> Tuple[str, dict]:
        data = {
            "source": self.source,
            "title": self.title,
            "link": self.link,
            "cleaned_content": self.cleaned_content,
            "date": self.date,
            "type": self.type
        }
        return self.entry_id, data

class Section(BaseModel):
    heading: str
    text: Optional[str] = None
    list: Optional[List[str]] = None

class Content(BaseModel):
    title: str
    sections: List[Section]

class Section(BaseModel):
    heading: str
    text: Optional[str] = None
    list: Optional[List[str]] = None

class Metadata(BaseModel):
    source: str
    author: Optional[str] = None
    last_updated: Optional[str] = None
    platform: str
    tags: Optional[List[str]] = None

class InvestopediaTermsCleanedModel(VectorDBDataModel):
    entry_id: str
    term: str
    url: str
    definition: str
    cleaned_content: str
    crawled_at: datetime = Field(default_factory=datetime.utcnow)
    type: str

    def to_payload(self) -> Tuple[str, dict]:
        data = {
            "term": self.term,
            "url": self.url,
            "definition": self.definition,
            "cleaned_content": self.cleaned_content,
            "crawled_at": self.crawled_at,
            "type": self.type
        }
        return self.entry_id, data

class MacroEconomicReportCleanedModel(VectorDBDataModel):
    entry_id: str
    date: datetime
    type: str
    cleaned_content: str
    crawled_at: datetime = Field(default_factory=datetime.utcnow)

    def to_payload(self) -> Tuple[str, dict]:
        data = {
            "date": self.date,
            "type": self.type,
            "cleaned_content": self.cleaned_content,
            "crawled_at": self.crawled_at
        }
        return self.entry_id, data
