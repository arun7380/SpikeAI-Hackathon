import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Define the project root directory for absolute path resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    """
    Application settings and environment variable management.
    """
    # LiteLLM Configuration (From provided hackathon assets)
    # hardcoded to the provided proxy URL per instructions
    LITELLM_BASE_URL: str = "http://3.110.18.218"
    LITELLM_API_KEY: str # Must be provided in .env
    
    # Model Configuration
    # Defaults to gemini-1.5-flash as per recommendation
    MODEL_NAME: str = "gemini-1.5-flash"

    # GA4 & SEO Configuration
    # Required for evaluator safety: credentials.json must be at root
    CREDENTIALS_JSON_PATH: Path = PROJECT_ROOT / "credentials.json"
    
    # SEO Public Sheet Link
    SEO_SHEET_URL: str = "https://docs.google.com/spreadsheets/d/1zzf4ax_H2WiTBVrJigGjF2Q3Yz-qy2qMCbAMKVI6VE E/edit#gid=1438203274"

    # Load from .env file at project root
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def validate_setup(self):
        """
        Safety check: Ensures credentials.json exists before the server starts.
        """
        if not self.CREDENTIALS_JSON_PATH.exists():
            raise FileNotFoundError(
                f"Required 'credentials.json' missing at {self.CREDENTIALS_JSON_PATH}. "
                "The evaluator will drop this file here during testing."
            )

# Instantiate settings once to be imported elsewhere
settings = Settings()