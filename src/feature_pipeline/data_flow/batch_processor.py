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
    PostsRawModel,
    ArticleRawModel,
    RepositoryRawModel,
    EdgarFillingRawModel,
    EarningsCallTranscriptRawModel
)
from feature_pipeline.data_logic.cleaning_data_handlers import (
    PostCleaningHandler,
    ArticleCleaningHandler,
    RepositoryCleaningHandler,
    EdgarFillingCleaningHandler,
    EarningsCallTranscriptCleaningHandler
)
from feature_pipeline.data_logic.chunking_data_handlers import (
    PostChunkingHandler,
    ArticleChunkingHandler,
    RepositoryChunkingHandler,
    EdgarFillingChunkingHandler,
    EarningsCallTranscriptChunkingHandler
)
from feature_pipeline.data_logic.embedding_data_handlers import (
    PostEmbeddingHandler,
    ArticleEmbeddingHandler,
    RepositoryEmbeddingHandler,
    EdgarFillingEmbeddingHandler,
    EarningsCallTranscriptEmbeddingHandler
)
from .batch_output import QdrantOutput, get_clean_collection, get_vector_collection

logger = get_logger(__name__)

_database = connection.get_database(settings.MONGO_DATABASE_NAME)

class BatchProcessor:
    def __init__(
        self,
        qdrant_connector: QdrantDatabaseConnector,
        batch_size: int = 100
    ):
        self.qdrant_connector = qdrant_connector
        self.batch_size = batch_size
        
        # Initialize handlers
        self.cleaning_handlers = {
            "posts": PostCleaningHandler(),
            "articles": ArticleCleaningHandler(),
            "repositories": RepositoryCleaningHandler(),
            "edgar_fillings": EdgarFillingCleaningHandler(),
            "earnings_call_transcripts": EarningsCallTranscriptCleaningHandler()
        }
        
        self.chunking_handlers = {
            "posts": PostChunkingHandler(),
            "articles": ArticleChunkingHandler(),
            "repositories": RepositoryChunkingHandler(),
            "edgar_fillings": EdgarFillingChunkingHandler(),
            "earnings_call_transcripts": EarningsCallTranscriptChunkingHandler()
        }
        
        self.embedding_handlers = {
            "posts": PostEmbeddingHandler(),
            "articles": ArticleEmbeddingHandler(),
            "repositories": RepositoryEmbeddingHandler(),
            "edgar_fillings": EdgarFillingEmbeddingHandler(),
            "earnings_call_transcripts": EarningsCallTranscriptEmbeddingHandler()
        }

        # Initialize Qdrant outputs
        self.clean_output = QdrantOutput(connection=qdrant_connector, sink_type="clean")
        self.vector_output = QdrantOutput(connection=qdrant_connector, sink_type="vector")

    def process_collection(self, collection_name: str, data_type: str):
        """Process a single collection from MongoDB to Qdrant"""
        collection = _database[collection_name]
        last_id = None
        total_processed = 0
        
        logger.info(f"Starting batch processing for collection: {collection_name}")
        
        while True:
            # Get batch of documents
            query = {'_id': {'$gt': last_id}} if last_id else {}
            batch = list(collection.find(query).limit(self.batch_size))
            
            if not batch:
                break
                
            # Process batch
            self._process_batch(batch, data_type)
            
            # Update last_id for next batch
            last_id = batch[-1]['_id']
            total_processed += len(batch)
            
            logger.info(
                f"Processed batch of {len(batch)} documents. Total processed: {total_processed}",
                collection=collection_name
            )
            
            # Small delay to prevent overwhelming the system
            time.sleep(0.1)
        
        logger.info(
            f"Completed processing collection: {collection_name}. Total documents: {total_processed}"
        )

    def _process_batch(self, batch: List[Dict[str, Any]], data_type: str):
        """Process a single batch of documents through the pipeline"""
        try:
            # Get appropriate handlers
            cleaning_handler = self.cleaning_handlers[data_type]
            chunking_handler = self.chunking_handlers[data_type]
            embedding_handler = self.embedding_handlers[data_type]
            
            # Process each document in the batch
            cleaned_items = []
            for doc in batch:
                # Convert MongoDB _id to entry_id and create appropriate model
                doc['entry_id'] = str(doc.pop('_id'))
                
                # Create appropriate raw model based on data type
                if data_type == "posts":
                    doc["type"] = data_type
                    raw_model = PostsRawModel(**doc)
                elif data_type == "articles":
                    doc["type"] = data_type
                    raw_model = ArticleRawModel(**doc)
                elif data_type == "repositories":
                    doc["type"] = data_type
                    raw_model = RepositoryRawModel(**doc)
                elif data_type == "edgar_fillings":
                    doc["type"] = data_type
                    raw_model = EdgarFillingRawModel(**doc)
                elif data_type == "earnings_call_transcripts":
                    doc["type"] = data_type
                    raw_model = EarningsCallTranscriptRawModel(**doc)
                else:
                    raise ValueError(f"Unsupported data type: {data_type}")
                
                # Clean
                cleaned_data = cleaning_handler.clean(raw_model)
                cleaned_items.append(cleaned_data)
            
            # Store cleaned data in batch
            if cleaned_items:
                self.clean_output.build(0, 1).write_batch(cleaned_items)
            
            # Process chunks and embeddings
            for cleaned_item in cleaned_items:
                # Chunk
                chunks = chunking_handler.chunk(cleaned_item)
                
                # Embed chunks
                embedded_chunks = []
                for chunk in chunks:
                    embedded_chunk = embedding_handler.embedd(chunk)
                    embedded_chunks.append(embedded_chunk)
                
                # Store embedded chunks in batch
                if embedded_chunks:
                    self.vector_output.build(0, 1).write_batch(embedded_chunks)
                    
        except Exception as e:
            logger.error(
                f"Error processing batch",
                error=str(e),
                data_type=data_type
            )
            raise 