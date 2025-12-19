import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Hackathon LiteLLM Config
    LITELLM_API_KEY: str = os.getenv("LITELLM_API_KEY", "sk-QY6sNLeECYNjzdtyJR8tyw")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-1.5-flash") # Fixed from 2.5 to 1.5
    LITELLM_BASE_URL: str = os.getenv("LITELLM_BASE_URL", "http://3.110.18.218")

    # Your Specific Data Identifiers
    DEFAULT_GA4_PROPERTY_ID: str = "516810413"
    DEFAULT_SHEET_ID: str = "1zzf4ax_H2WiTBVrJigGjF2Q3Yz-qy2qMCbAMKvl6VEE"
    
    # Path to the credentials file you just added to root
    GOOGLE_APPLICATION_CREDENTIALS: str = os.path.join(os.getcwd(), "credentials.json")

    # Server Config
    PORT: int = 8080
    HOST: str = "0.0.0.0"

settings = Settings()