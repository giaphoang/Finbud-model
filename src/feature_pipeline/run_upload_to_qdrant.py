import os
from core import get_logger
from core.db.qdrant import QdrantDatabaseConnector
from feature_pipeline.data_flow.qdrant_processor import QdrantProcessor
from config import settings

logger = get_logger(__name__)

def main():
    # Initialize Qdrant connector with cloud credentials
    qdrant_connector = QdrantDatabaseConnector()
    
    # Initialize batch processor
    processor = QdrantProcessor(
        qdrant_connector=qdrant_connector,
        batch_size=100  # Adjust based on your needs
    )
    
    try:
        # Process each collection
        collections_to_process = [
            ("edgar_fillings", "edgar_fillings"),
            # ("earnings_call_transcripts", "earnings_call_transcripts"),
            # ("yahoo", "yahoo"),
            # ("bloomberg", "bloomberg"),
            # ("investopedia_personal_finance", "investopedia_personal_finance"),
            # ("investopedia_terms", "investopedia_terms"),
            # ("macro_economic_reports", "macro_economic_reports")
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