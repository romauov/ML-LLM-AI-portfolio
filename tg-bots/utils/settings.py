"""
секреты клиента ChatGPT

@author Sergei Romanov
"""
from dotenv import load_dotenv
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class MeatInfoSettings(BaseSettings):
    price_id: str
    reglament: str
    channel_id: str
    admin_ids: List[int]
    manager_ids: List[int]
    token: str


class EdelweisSettings(BaseSettings):
    reglament: str
    channel_id: str
    admin_ids: List[int]
    manager_ids: List[int]
    token: str


class ShaurmatikaSettings(BaseSettings):
    reglament: str
    channel_id: str
    admin_ids: List[int]
    manager_ids: List[int]
    token: str


class SeleznevaSettings(BaseSettings):
    price_id: str
    reglament: str
    channel_id: str
    admin_ids: List[int]
    manager_ids: List[int]
    token: str


class TorgKitSettings(BaseSettings):
    reglament: str
    channel_id: str
    admin_ids: List[int]
    manager_ids: List[int]
    token: str


class NomadicEssenSettings(BaseSettings):
    reglament: str
    channel_id: str
    admin_ids: List[int]
    manager_ids: List[int]
    token: str

class MuksunSettings(BaseSettings):
    reglament: str
    channel_id: str
    admin_ids: List[int]
    manager_ids: List[int]
    token: str

class OpenAISettings(BaseSettings):
    key: str
    proxy: str
    organization: str
    project: str


class Secrets(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter='__')

    openai: OpenAISettings
    meatinfo: MeatInfoSettings
    edelweis: EdelweisSettings
    shaurmatika: ShaurmatikaSettings
    selezneva: SeleznevaSettings
    torgkit: TorgKitSettings
    nomadic_essen: NomadicEssenSettings
    muksun: MuksunSettings
    errors_channel_id: str


secrets = Secrets()
