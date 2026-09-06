from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_title: str = 'Events Aggregator'
    app_description: str = 'Special aggregator for Events Provider API'

    origins: Annotated[list[str], NoDecode] = ['*']

    update_interval_h: int = 24
    provider_base_url: str = 'http://events-provider.dev-2.python-labs.ru'
    provider_api_key: str = ''

    postgres_host: str = 'localhost'
    postgres_username: str = 'postgres'
    postgres_password: str = 'postgres'
    postgres_database_name: str = 'postgres'
    postgres_port: int = 5432

    @property
    def db_url(self) -> str:
        return (
            f'postgresql+asyncpg://{self.postgres_username}:{self.postgres_password}'
            f'@{self.postgres_host}:{self.postgres_port}/{self.postgres_database_name}'
        )

    @field_validator('origins', mode='before')
    @classmethod
    def decode_origins(cls, v: str) -> list[str]:
        if isinstance(v, list):
            return v
        return v.split(',')

    model_config = SettingsConfigDict(env_file='.env')


settings = Settings()
