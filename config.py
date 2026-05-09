"""Configuration module for daily stock analysis.

Loads environment variables and provides centralized configuration
for API keys, database settings, and analysis parameters.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Central configuration class for the stock analysis application."""

    # --- API Keys ---
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    TUSHARE_TOKEN: str = os.getenv("TUSHARE_TOKEN", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # --- Database Settings ---
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "stock_analysis")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    # --- Redis / Cache ---
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    # Increased TTL to 2 hours to reduce redundant API calls during my testing sessions
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "7200"))

    # --- Stock Analysis Parameters ---
    DEFAULT_MARKET: str = os.getenv("DEFAULT_MARKET", "CN")  # CN or US
    ANALYSIS_LOOKBACK_DAYS: int = int(os.getenv("ANALYSIS_LOOKBACK_DAYS", "30"))
    TOP_N_STOCKS: int = int(os.getenv("TOP_N_STOCKS", "10"))

    # Moving average windows
    MA_SHORT_WINDOW: int = int(os.getenv("MA_SHORT_WINDOW", "5"))
    MA_MEDIUM_WINDOW: int = int(os.getenv("MA_MEDIUM_WINDOW", "20"))
    MA_LONG_WINDOW: int = int(os.getenv("MA_LONG_WINDOW", "60"))

    # RSI settings
    RSI_PERIOD: int = int(os.getenv("RSI_PERIOD", "14"))
    RSI_OVERBOUGHT: float = float(os.getenv("RSI_OVERBOUGHT", "70"))
    RSI_OVERSOLD: float = float(os.getenv("RSI_OVERSOLD", "30"))

    # --- Notification Settings ---
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    EMAIL_SMTP_HOST: str = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
    EMAIL_SMTP_PORT: int = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_RECIPIENTS: list = [
        r.strip()
        for r in os.getenv("EMAIL_RECIPIENTS", "").split(",")
        if r.strip()
    ]

    # --- Output Settings ---
    REPORT_OUTPUT_DIR: str = os.getenv("REPORT_OUTPUT_DIR", "./reports")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "./logs/stock_analysis.log")

    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration values are set.

        Raises:
            ValueError: If any required configuration is missing.
        """
        errors = []

        if not cls.TUSHARE_TOKEN and not cls.ALPHA_VANTAGE_API_KEY:
            errors.append(
                "At least one data source API key is required: "
                "TUSHARE_
