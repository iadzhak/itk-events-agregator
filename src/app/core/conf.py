from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_title: str = 'Events Aggregator'
    app_description: str = 'Special aggregator for Events Provider API'

    check_interval: int = 60

    origins: Annotated[list[str], NoDecode] = ['*']

    db_host: str = 'localhost'
    postgres_user: str = 'postgres'
    postgres_password: str = 'postgres'
    postgres_db: str = 'postgres'
    postgres_port: int = 5432

    @property
    def db_url(self) -> str:
        return (
            f'postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}'
            f'@{self.db_host}:{self.postgres_port}/{self.postgres_db}'
        )

    @field_validator('origins', mode='before')
    @classmethod
    def decode_origins(cls, v: str) -> list[str]:
        if isinstance(v, list):
            return v
        return v.split(',')

    model_config = SettingsConfigDict(env_file='.env')


settings = Settings()
