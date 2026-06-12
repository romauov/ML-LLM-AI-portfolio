"""
Парсинг .env файла.

@author Nikolay Zhabchikov
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
    db_table_raw_meat: str
    db_table_forecasting_history: str
    db_table_predicted_price: str
    api_user: str
    api_password: str
    db_raw_seafood_table_name: str
    db_raw_caviar_table_name: str
    db_raw_fish_table_name: str
    db_raw_shrimp_table_name: str
    db_raw_semiprocessed_table_name: str

    class Config:
        extra = 'ignore'
        env_file = ".env"
        env_file_encoding = "utf-8"


secrets = Secrets()
