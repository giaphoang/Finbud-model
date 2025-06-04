from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = str(Path(__file__).parent.parent.parent)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR, env_file_encoding="utf-8")

    # CometML config
    COMET_API_KEY: str | None = None
    COMET_WORKSPACE: str | None = None
    COMET_PROJECT: str = "llm-twin"

    # Embeddings config
    EMBEDDING_MODEL_ID: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_MODEL_MAX_INPUT_LENGTH: int = 512
    EMBEDDING_SIZE: int = 384
    EMBEDDING_MODEL_DEVICE: str = "cpu"

    # OpenAI
    OPENAI_MODEL_ID: str = "gpt-4o-mini"
    OPENAI_API_KEY: str | None = None

    # Groq
    GROQ_API_KEY: str | None = None
    GROQ_MODEL_ID: str = "llama3-8b-8192"

    # MQ config
    RABBITMQ_DEFAULT_USERNAME: str = "guest"
    RABBITMQ_DEFAULT_PASSWORD: str = "guest"
    RABBITMQ_HOST: str = "mq"  # or localhost if running outside Docker
    RABBITMQ_PORT: int = 5672
    RABBITMQ_QUEUE_NAME: str = "default"

    # QdrantDB config
    QDRANT_DATABASE_HOST: str = "qdrant"  # or localhost if running outside Docker
    QDRANT_DATABASE_PORT: int = 6333
    USE_QDRANT_CLOUD: bool = (
        False  # if True, fill in QDRANT_CLOUD_URL and QDRANT_APIKEY
    )
    QDRANT_CLOUD_URL: str | None = "https://de3e8544-198a-45c1-a8f4-1f8da581443e.us-east-1-0.aws.cloud.qdrant.io"
    QDRANT_CLOUD_API_KEY: str | None = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.Q0A0aKlTd95cD5U0Bnl2tVB3RTb3jw9CkKApUTRwxmM"
    MONGO_DATABASE_URI: str = "mongodb+srv://giaptomhoang:mMmbProbiaB0bI3a@finbud-model.w2otx5f.mongodb.net/?retryWrites=true&w=majority&appName=Finbud-model"
    MONGO_DATABASE_NAME: str = "twin"

settings = Settings()
