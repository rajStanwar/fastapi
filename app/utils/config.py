from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

class Settings(BaseSettings):
    mongo_uri: str
    root_path: str = ""
    logging_level: str = "INFO"
    model_config: SettingsConfigDict(env_file=".env", extra="ignore")
    

settings = Settings()
