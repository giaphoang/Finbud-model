import os
from core import get_logger
from core.db.qdrant import QdrantDatabaseConnector
from data_flow.batch_processor import BatchProcessor
from config import settings

logger = get_logger(__name__)

def main():
    # Initialize Qdrant connector with cloud credentials
    qdrant_connector = QdrantDatabaseConnector()
    
    # Initialize batch processor
    processor = BatchProcessor(
        qdrant_connector=qdrant_connector,
        batch_size=100  # Adjust based on your needs
    )
    
    try:
        # Process each collection
        collections_to_process = [
            # ("edgar_fillings", "edgar_fillings"),
            ("earnings_call_transcripts", "earnings_call_transcripts")
        ]
        
        for collection_name, data_type in collections_to_process:
            logger.info(f"Starting processing for {collection_name}")
            processor.process_collection(collection_name, data_type)
            logger.info(f"Completed processing for {collection_name}")
            
    except Exception as e:
        logger.error(f"Error during batch processing: {str(e)}")
        raise

if __name__ == "__main__":
    main() 