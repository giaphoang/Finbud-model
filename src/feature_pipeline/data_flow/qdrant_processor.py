from typing import List, Optional, Dict, Any
from datetime import datetime
import time
from core import get_logger
from core.db.mongo import connection
from core.db.qdrant import QdrantDatabaseConnector
from core.config import settings
from qdrant_client.models import Batch
from models.base import VectorDBDataModel
from models.raw import (
    EdgarFillingRawModel,
    EarningsCallTranscriptRawModel,
    YahooFinanceRawModel,
    BloombergRawModel,
    InvestopediaPersonalFinanceRawModel,
    InvestopediaTermsRawModel,
    MacroEconomicReportRawModel
)
from feature_pipeline.data_logic.cleaning_data_handlers import (
    EdgarFillingCleaningHandler,
    EarningsCallTranscriptCleaningHandler,
    YahooFinanceCleaningHandler,
    BloombergCleaningHandler,
    InvestopediaPersonalFinanceCleaningHandler,
    InvestopediaTermsCleaningHandler,
    MacroEconomicReportCleaningHandler
)
from feature_pipeline.data_logic.chunking_data_handlers import (
    EdgarFillingChunkingHandler,
    EarningsCallTranscriptChunkingHandler,
    YahooFinanceChunkingHandler,
    BloombergChunkingHandler,
    InvestopediaPersonalFinanceChunkingHandler,
    InvestopediaTermsChunkingHandler,
    MacroEconomicReportChunkingHandler
)
from feature_pipeline.data_logic.embedding_data_handlers import (
    EdgarFillingEmbeddingHandler,
    EarningsCallTranscriptEmbeddingHandler,
    YahooFinanceEmbeddingHandler,
    BloombergEmbeddingHandler,
    InvestopediaPersonalFinanceEmbeddingHandler,
    InvestopediaTermsEmbeddingHandler,
    MacroEconomicReportEmbeddingHandler
)
from .qdrant_output import QdrantOutput, get_clean_collection, get_vector_collection

logger = get_logger(__name__)

_database = connection.get_database(settings.MONGO_DATABASE_NAME)

class QdrantProcessor:
    def __init__(
        self,
        qdrant_connector: QdrantDatabaseConnector,
        batch_size: int = 100
    ):
        self.qdrant_connector = qdrant_connector
        self.batch_size = batch_size
        
        # Initialize handlers
        self.cleaning_handlers = {
            "edgar_fillings": EdgarFillingCleaningHandler(),
            "earnings_call_transcripts": EarningsCallTranscriptCleaningHandler(),
            "yahoo": YahooFinanceCleaningHandler(),
            "bloomberg": BloombergCleaningHandler(),
            "investopedia_personal_finance": InvestopediaPersonalFinanceCleaningHandler(),
            "investopedia_terms": InvestopediaTermsCleaningHandler(),
            "macro_economic_reports": MacroEconomicReportCleaningHandler()
        }
        
        self.chunking_handlers = {
            "edgar_fillings": EdgarFillingChunkingHandler(),
            "earnings_call_transcripts": EarningsCallTranscriptChunkingHandler(),
            "yahoo": YahooFinanceChunkingHandler(),
            "bloomberg": BloombergChunkingHandler(),
            "investopedia_personal_finance": InvestopediaPersonalFinanceChunkingHandler(),
            "investopedia_terms": InvestopediaTermsChunkingHandler(),
            "macro_economic_reports": MacroEconomicReportChunkingHandler()
        }
        
        self.embedding_handlers = {
            "edgar_fillings": EdgarFillingEmbeddingHandler(),
            "earnings_call_transcripts": EarningsCallTranscriptEmbeddingHandler(),
            "yahoo": YahooFinanceEmbeddingHandler(),
            "bloomberg": BloombergEmbeddingHandler(),
            "investopedia_personal_finance": InvestopediaPersonalFinanceEmbeddingHandler(),
            "investopedia_terms": InvestopediaTermsEmbeddingHandler(),
            "macro_economic_reports": MacroEconomicReportEmbeddingHandler()
        }

        # Initialize Qdrant outputs
        self.clean_output = QdrantOutput(connection=qdrant_connector, sink_type="clean")
        self.vector_output = QdrantOutput(connection=qdrant_connector, sink_type="vector")

    def process_collection(self, collection_name: str, data_type: str):
        """Process a single collection from MongoDB to Qdrant"""
        if data_type not in self.cleaning_handlers:
            raise ValueError(f"Unsupported data type: {data_type}")

        collection = _database[collection_name]
        total_processed = 0
        total_errors = 0
        max_retries = 3
        
        # Get total document count for progress tracking
        total_docs = collection.count_documents({})
        logger.info(
            f"Starting processing for collection: {collection_name}",
            total_documents=total_docs
        )
        
        # Process documents with retry logic
        while total_processed < total_docs:
            try:
                # Create a cursor with no timeout and explicit batch size
                cursor = collection.find().max_time_ms(200000)  # 2 minutes timeout
                
                for doc in cursor:
                    try:
                        # Convert MongoDB _id to entry_id and create appropriate model
                        doc['entry_id'] = str(doc.pop('_id'))
                        doc['type'] = data_type
                        
                        # Create appropriate raw model based on data type
                        raw_model = self._create_raw_model(doc, data_type)
                        
                        # Get appropriate handlers
                        cleaning_handler = self.cleaning_handlers[data_type]
                        chunking_handler = self.chunking_handlers[data_type]
                        embedding_handler = self.embedding_handlers[data_type]
                        
                        # Clean
                        cleaned_data = cleaning_handler.clean(raw_model)
                        
                        # Store cleaned data
                        self.clean_output.build(0, 1).write_batch([cleaned_data])
                        
                        # Chunk
                        chunks = chunking_handler.chunk(cleaned_data)
                        
                        # Embed chunks
                        embedded_chunks = []
                        for chunk in chunks:
                            embedded_chunk = embedding_handler.embedd(chunk)
                            embedded_chunks.append(embedded_chunk)
                        
                        # Store embedded chunks
                        if embedded_chunks:
                            self.vector_output.build(0, 1).write_batch(embedded_chunks)
                        
                        total_processed += 1
                        
                        # Log progress periodically (every 100 documents)
                        if total_processed % 100 == 0:
                            progress = (total_processed / total_docs) * 100
                            logger.info(
                                f"Processed {total_processed} documents. "
                                f"Progress: {progress:.2f}% ({total_processed}/{total_docs})",
                                collection=collection_name,
                                errors=total_errors
                            )
                        
                    except Exception as e:
                        total_errors += 1
                        logger.error(
                            f"Error processing document",
                            error=str(e),
                            doc_id=doc.get('_id'),
                            collection=collection_name
                        )
                        continue
                
                # If we get here, we've successfully processed all documents
                break
                
            except Exception as e:
                if "CursorNotFound" in str(e):
                    logger.warning(
                        f"Cursor not found, retrying... (Attempt {max_retries})",
                        error=str(e),
                        collection=collection_name
                    )
                    max_retries -= 1
                    if max_retries <= 0:
                        logger.error(
                            f"Max retries exceeded, stopping processing",
                            collection=collection_name,
                            processed=total_processed,
                            errors=total_errors
                        )
                        raise
                    time.sleep(1)  # Wait before retrying
                    continue
                else:
                    logger.error(
                        f"Unexpected error during processing",
                        error=str(e),
                        collection=collection_name
                    )
                    raise
        
        logger.info(
            f"Completed processing collection: {collection_name}. "
            f"Total documents: {total_processed}/{total_docs}, "
            f"Total errors: {total_errors}, "
            f"Success rate: {((total_processed - total_errors) / total_docs) * 100:.2f}%"
        )

    def _create_raw_model(self, doc: Dict[str, Any], data_type: str) -> Any:
        """Create appropriate raw model based on data type"""
        if data_type == "edgar_fillings":
            return EdgarFillingRawModel(**doc)
        elif data_type == "earnings_call_transcripts":
            return EarningsCallTranscriptRawModel(**doc)
        elif data_type == "yahoo":
            return YahooFinanceRawModel(**doc)
        elif data_type == "bloomberg":
            return BloombergRawModel(**doc)
        elif data_type == "investopedia_personal_finance":
            return InvestopediaPersonalFinanceRawModel(**doc)
        elif data_type == "investopedia_terms":
            return InvestopediaTermsRawModel(**doc)
        elif data_type == "macro_economic_reports":
            return MacroEconomicReportRawModel(**doc)
        else:
            raise ValueError(f"Unsupported data type: {data_type}") 