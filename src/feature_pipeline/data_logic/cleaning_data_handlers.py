from abc import ABC, abstractmethod
from typing import Any
from models.base import DataModel
from models.clean import EdgarFillingCleanedModel, EarningsCallTranscriptCleanedModel, FinancialNewsCleanedModel, InvestopediaTermsCleanedModel, MacroEconomicReportCleanedModel
from models.raw import EdgarFillingRawModel, EarningsCallTranscriptRawModel, FinancialNewsRawModel, InvestopediaTermsRawModel, MacroEconomicReportRawModel
from utils.cleaning import clean_text


def flatten_content(content) -> str:
    parts = [content.title]
    for section in content.sections:
        if getattr(section, 'heading', None):
            parts.append(section.heading)
        if getattr(section, 'text', None):
            parts.append(section.text)
        if getattr(section, 'list', None):
            parts.extend(section.list)
    return "\n".join([str(p) for p in parts if p])


class CleaningDataHandler(ABC):
    """
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
    
class FinancialNewsCleaningHandler(CleaningDataHandler):
    def clean(self, raw_data: FinancialNewsRawModel) -> FinancialNewsCleanedModel:
        return FinancialNewsCleanedModel(
            entry_id=raw_data.entry_id,
            type=raw_data.type,
            source=raw_data.source,
            title=raw_data.title,
            link=raw_data.link,
            cleaned_content=clean_text(raw_data.summary),
            date=raw_data.date
        )

class InvestopediaTermsCleaningHandler(CleaningDataHandler):
    def clean(self, raw_data: InvestopediaTermsRawModel) -> InvestopediaTermsCleanedModel:
        # First clean the definition
        cleaned_definition = clean_text(raw_data.definition)
        
        # Then clean the content sections
        content_str = ""
        if raw_data.content:
            content_str = flatten_content(raw_data.content)
            content_str = clean_text(content_str)
        
        # Combine both cleaned texts
        cleaned_content = f"{cleaned_definition}\n\n{content_str}".strip()
        
        return InvestopediaTermsCleanedModel(
            entry_id=raw_data.entry_id,
            type=raw_data.type,
            term=raw_data.term,
            url=raw_data.url,
            definition=raw_data.definition,
            cleaned_content=cleaned_content,
            crawled_at=raw_data.crawled_at
        )

class MacroEconomicReportCleaningHandler(CleaningDataHandler):
    def clean(self, raw_data: MacroEconomicReportRawModel) -> MacroEconomicReportCleanedModel:
        content_str = flatten_content(raw_data.content)
        return MacroEconomicReportCleanedModel(
            entry_id=raw_data.entry_id,
            type=raw_data.type,
            date=raw_data.date,
            cleaned_content=clean_text(content_str),
            crawled_at=raw_data.crawled_at
        )
