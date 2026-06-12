"""
секреты клиента ChatGPT

@author Sergei Romanov
"""
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Secrets(BaseSettings):
    openai_key: str
    openai_proxy: str
    
    db_user: str
    db_password: str
    db_host: str
    db_name: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


secrets = Secrets()
