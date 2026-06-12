"""
учётные данные проекта

@author Sergei Romanov
"""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Secrets(BaseSettings):
    db_user: str
    db_password: str
    db_host: str
    db_port: str
    db_name: str
    raw_table_meat: str
    raw_table_fish: str
    raw_table_caviar: str
    raw_table_shrimp: str
    raw_table_seafood: str
    raw_table_semiprocessed: str
    raw_table_milk: str
    raw_table_egg: str
    raw_table_fruit: str

    tg_token: str
    notifications_channel: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = 'ignore'


secrets = Secrets()
