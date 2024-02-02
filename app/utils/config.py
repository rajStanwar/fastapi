from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

class Settings(BaseSettings):
    mongo_uri: str
    client_id: str
    client_secret: str
    root_path: str = ""
    logging_level: str = "INFO"
    testing: bool = False
    model_config: SettingsConfigDict(env_file=".env", extra="ignore")
    

settings = Settings()
