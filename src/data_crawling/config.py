from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = str(Path(__file__).parent.parent.parent)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR, env_file_encoding="utf-8")

    MONGO_DATABASE_HOST: str = (
        "mongodb+srv://giaptomhoang:mMmbProbiaB0bI3a@finbud-model.w2otx5f.mongodb.net/?retryWrites=true&w=majority&appName=Finbud-model"
    )
    MONGO_DATABASE_NAME: str = "twin"

settings = Settings()
