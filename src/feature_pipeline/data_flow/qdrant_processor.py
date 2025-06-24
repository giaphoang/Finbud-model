from typing import List, Optional, Dict, Any
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
    FinancialNewsRawModel,
    InvestopediaTermsRawModel,
    MacroEconomicReportRawModel
)
from feature_pipeline.data_logic.cleaning_data_handlers import (
    EdgarFillingCleaningHandler,
    EarningsCallTranscriptCleaningHandler,
    FinancialNewsCleaningHandler,
    InvestopediaTermsCleaningHandler,
    MacroEconomicReportCleaningHandler
)
from feature_pipeline.data_logic.chunking_data_handlers import (
    EdgarFillingChunkingHandler,
    EarningsCallTranscriptChunkingHandler,
    FinancialNewsChunkingHandler,
    InvestopediaTermsChunkingHandler,
    MacroEconomicReportChunkingHandler
)
from feature_pipeline.data_logic.embedding_data_handlers import (
    EdgarFillingEmbeddingHandler,
    EarningsCallTranscriptEmbeddingHandler,
    FinancialNewsEmbeddingHandler,
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
        batch_size: int = 50
    ):
        self.qdrant_connector = qdrant_connector
        self.batch_size = batch_size
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
        # Initialize handlers
        self.cleaning_handlers = {
            "edgar_fillings": EdgarFillingCleaningHandler(),
            "earnings_call_transcripts": EarningsCallTranscriptCleaningHandler(),
            "financial_news": FinancialNewsCleaningHandler(),
            "investopedia": InvestopediaTermsCleaningHandler(),
            "macro_economic_reports": MacroEconomicReportCleaningHandler()
        }
        
        self.chunking_handlers = {
            "edgar_fillings": EdgarFillingChunkingHandler(),
            "earnings_call_transcripts": EarningsCallTranscriptChunkingHandler(),
            "financial_news": FinancialNewsChunkingHandler(),
            "investopedia": InvestopediaTermsChunkingHandler(),
            "macro_economic_reports": MacroEconomicReportChunkingHandler()
        }
        
        self.embedding_handlers = {
            "edgar_fillings": EdgarFillingEmbeddingHandler(),
            "earnings_call_transcripts": EarningsCallTranscriptEmbeddingHandler(),
            "financial_news": FinancialNewsEmbeddingHandler(),
            "investopedia": InvestopediaTermsEmbeddingHandler(),
            "macro_economic_reports": MacroEconomicReportEmbeddingHandler()
        }

        # Initialize Qdrant outputs
        self.clean_output = QdrantOutput(connection=qdrant_connector, sink_type="clean")
        self.vector_output = QdrantOutput(connection=qdrant_connector, sink_type="vector")

    def _write_with_retry(self, output, items, retry_count=0):
        """Helper method to write data with retry logic"""
        try:
            output.build(0, 1).write_batch(items)
        except Exception as e:
            if retry_count < self.max_retries:
                # Calculate exponential backoff delay
                delay = self.retry_delay * (2 ** retry_count)
                logger.warning(
                    f"Write operation failed, retrying... (Attempt {retry_count + 1}/{self.max_retries})",
                    error=str(e),
                    delay=delay
                )
                time.sleep(delay)
                return self._write_with_retry(output, items, retry_count + 1)
            else:
                logger.error(
                    f"Max retries exceeded for write operation",
                    error=str(e),
                    items_count=len(items)
                )
                raise

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
        
        # Process documents in smaller batches
        batch_size = 25  # Reduced batch size to prevent timeouts
        
        # Process documents in batches
        while total_processed < total_docs:
            try:
                # Create a cursor with a smaller timeout and explicit batch size
                cursor = collection.find().skip(total_processed).limit(batch_size).max_time_ms(30000)  # 30 second timeout
                
                batch_docs = list(cursor)  # Convert cursor to list immediately to avoid timeout issues
                if not batch_docs:
                    break
                
                for doc in batch_docs:
                    try:
                        # Convert MongoDB _id to entry_id and create appropriate model
                        doc['entry_id'] = str(doc.pop('_id'))
                        doc['type'] = data_type
                        
                        doc.pop("metadata", None)
                        
                        # Create appropriate raw model based on data type
                        raw_model = self._create_raw_model(doc, data_type)
                        
                        # Get appropriate handlers
                        cleaning_handler = self.cleaning_handlers[data_type]
                        chunking_handler = self.chunking_handlers[data_type]
                        embedding_handler = self.embedding_handlers[data_type]
                        
                        # Clean
                        cleaned_data = cleaning_handler.clean(raw_model)
                        
                        # Store cleaned data with retry
                        self._write_with_retry(self.clean_output, [cleaned_data])
                        
                        # Chunk
                        chunks = chunking_handler.chunk(cleaned_data)
                        
                        # Process chunks in smaller sub-batches
                        chunk_batch_size = 5  # Reduced chunk batch size
                        for i in range(0, len(chunks), chunk_batch_size):
                            chunk_batch = chunks[i:i + chunk_batch_size]
                        
                            # Embed chunks
                            embedded_chunks = []
                            for chunk in chunk_batch:
                                try:
                                    embedded_chunk = embedding_handler.embedd(chunk)
                                    embedded_chunks.append(embedded_chunk)
                                except Exception as e:
                                    logger.error(
                                        f"Error embedding chunk",
                                        error=str(e),
                                        doc_id=doc.get('entry_id'),
                                        chunk_id=chunk.chunk_id
                                    )
                                    continue
                            
                            # Store embedded chunks with retry, but in smaller batches
                            if embedded_chunks:
                                # Split into even smaller batches for Qdrant writes
                                qdrant_batch_size = 3  # Very small batch size for Qdrant writes
                                for j in range(0, len(embedded_chunks), qdrant_batch_size):
                                    qdrant_batch = embedded_chunks[j:j + qdrant_batch_size]
                                    try:
                                        self._write_with_retry(self.vector_output, qdrant_batch)
                                    except Exception as e:
                                        logger.error(
                                            f"Failed to write batch to Qdrant after retries",
                                            error=str(e),
                                            doc_id=doc.get('entry_id'),
                                            batch_size=len(qdrant_batch)
                                        )
                                        # Continue processing other batches even if one fails
                                        continue
                        
                        total_processed += 1
                        
                        # Log progress more frequently (every 50 documents)
                        if total_processed % 50 == 0:
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
                            doc_id=doc.get('entry_id'),
                            collection=collection_name
                        )
                        continue
                
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
        elif data_type == "financial_news":
            return FinancialNewsRawModel(**doc)
        elif data_type == "investopedia":
            return InvestopediaTermsRawModel(**doc)
        elif data_type == "macro_economic_reports":
            return MacroEconomicReportRawModel(**doc)
        else:
            raise ValueError(f"Unsupported data type: {data_type}") 