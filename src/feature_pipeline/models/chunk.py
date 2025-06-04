from typing import Optional

from models.base import DataModel


class PostChunkModel(DataModel):
    entry_id: str
    platform: str
    chunk_id: str
    chunk_content: str
    author_id: str
    image: Optional[str] = None
    type: str


class ArticleChunkModel(DataModel):
    entry_id: str
    platform: str
    link: str
    chunk_id: str
    chunk_content: str
    author_id: str
    type: str


class RepositoryChunkModel(DataModel):
    entry_id: str
    name: str
    link: str
    chunk_id: str
    chunk_content: str
    owner_id: str
    type: str


class EdgarFillingChunkModel(DataModel):
    entry_id: str
    source: str
    url: str
    date: str
    ticker: str
    chunk_id: str
    chunk_content: str
    type: str


class EarningsCallTranscriptChunkModel(DataModel):
    entry_id: str
    source: str
    url: str
    date: str
    chunk_id: str
    chunk_content: str
    type: str
