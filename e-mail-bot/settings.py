"""
секреты проекта

@author Sergei Romanov
"""
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv() 

class Secrets(BaseSettings):  
 
    ai_m16_url: str
    ai_m16_user: str 
    ai_m16_password: str
    
    openai_proxy: str
    openai_key: str
    
    class Config:  
        env_file = ".env"  
        env_file_encoding = "utf-8"


secrets = Secrets()
