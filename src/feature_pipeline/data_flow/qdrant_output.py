from bytewax.outputs import DynamicSink, StatelessSinkPartition
from core import get_logger
from core.db.qdrant import QdrantDatabaseConnector
from models.base import VectorDBDataModel
from qdrant_client.models import Batch

logger = get_logger(__name__)


class QdrantOutput(DynamicSink):
    """
    Bytewax class that facilitates the connection to a Qdrant vector DB.
    Inherits DynamicSink because of the ability to create different sink sources (e.g, vector and non-vector collections)
    """

    def __init__(self, connection: QdrantDatabaseConnector, sink_type: str):
        self._connection = connection
        self._sink_type = sink_type

        collections = {
            "cleaned_edgar_fillings": False,
            "cleaned_earnings_call_transcripts": False,
            "cleaned_yahoo": False,
            "cleaned_bloomberg": False,
            "cleaned_investopedia_personal_finance": False,
            "cleaned_investopedia_terms": False,
            "cleaned_macro_economic_reports": False,

            "vector_edgar_fillings": True,
            "vector_earnings_call_transcripts": True,
            "vector_yahoo": True,
            "vector_bloomberg": True,
            "vector_investopedia_personal_finance": True,
            "vector_investopedia_terms": True,
            "vector_macro_economic_reports": True,
        }

        for collection_name, is_vector in collections.items():
            try:
                self._connection.get_collection(collection_name=collection_name)
            except Exception:
                logger.warning(
                    "Couldn't access the collection. Creating a new one...",
                    collection_name=collection_name,
                )

                if is_vector:
                    self._connection.create_vector_collection(
                        collection_name=collection_name
                    )
                else:
                    self._connection.create_non_vector_collection(
                        collection_name=collection_name
                    )

    def build(self, worker_index: int, worker_count: int) -> StatelessSinkPartition:
        if self._sink_type == "clean":
            return QdrantCleanedDataSink(connection=self._connection)
        elif self._sink_type == "vector":
            return QdrantVectorDataSink(connection=self._connection)
        else:
            raise ValueError(f"Unsupported sink type: {self._sink_type}")


class QdrantCleanedDataSink(StatelessSinkPartition):
    def __init__(self, connection: QdrantDatabaseConnector):
        self._client = connection

    def write_batch(self, items: list[VectorDBDataModel]) -> None:
        payloads = [item.to_payload() for item in items]
        ids, data = zip(*payloads)
        collection_name = get_clean_collection(data_type=data[0]["type"])
        self._client.write_data(
            collection_name=collection_name,
            points=Batch(ids=ids, vectors={}, payloads=data),
        )

        logger.info(
            "Successfully inserted requested cleaned point(s)",
            collection_name=collection_name,
            num=len(ids),
        )


class QdrantVectorDataSink(StatelessSinkPartition):
    def __init__(self, connection: QdrantDatabaseConnector):
        self._client = connection

    def write_batch(self, items: list[VectorDBDataModel]) -> None:
        payloads = [item.to_payload() for item in items]
        ids, vectors, meta_data = zip(*payloads)
        collection_name = get_vector_collection(data_type=meta_data[0]["type"])
        self._client.write_data(
            collection_name=collection_name,
            points=Batch(ids=ids, vectors=vectors, payloads=meta_data),
        )

        logger.info(
            "Successfully inserted requested vector point(s)",
            collection_name=collection_name,
            num=len(ids),
        )


def get_clean_collection(data_type: str) -> str:
    if data_type == "edgar_fillings":
        return "cleaned_edgar_fillings"
    elif data_type == "earnings_call_transcripts":
        return "cleaned_earnings_call_transcripts"
    elif data_type == "yahoo":
        return "cleaned_yahoo"
    elif data_type == "bloomberg":
        return "cleaned_bloomberg"
    elif data_type == "investopedia_personal_finance":
        return "cleaned_investopedia_personal_finance"
    elif data_type == "investopedia_terms":
        return "cleaned_investopedia_terms"
    elif data_type == "macro_economic_reports":
        return "cleaned_macro_economic_reports"
    else:
        raise ValueError(f"Unsupported data type: {data_type}")


def get_vector_collection(data_type: str) -> str:
    if data_type == "edgar_fillings":
        return "vector_edgar_fillings"
    elif data_type == "earnings_call_transcripts":
        return "vector_earnings_call_transcripts"
    elif data_type == "yahoo":
        return "vector_yahoo"
    elif data_type == "bloomberg":
        return "vector_bloomberg"
    elif data_type == "investopedia_personal_finance":
        return "vector_investopedia_personal_finance"
    elif data_type == "investopedia_terms":
        return "vector_investopedia_terms"
    elif data_type == "macro_economic_reports":
        return "vector_macro_economic_reports"
    else:
        raise ValueError(f"Unsupported data type: {data_type}")
