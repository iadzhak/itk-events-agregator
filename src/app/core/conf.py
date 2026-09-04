from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_title: str = 'Events Aggregator'
    app_description: str = 'Special aggregator for Events Provider API'

    check_interval: int = 60

    origins: Annotated[list[str], NoDecode] = '*'

    @field_validator('origins', mode='before')
    @classmethod
    def decode_origins(cls, v: str) -> list[str]:
        return v.split(',')

    model_config = SettingsConfigDict(env_file='.env')


settings = Settings()
