"""
Central configuration for the test suite.
Values can be overridden via environment variables or a .env file.
"""
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL: str = os.getenv("BASE_URL", "https://qae-assignment-tau.vercel.app")
USER_ID: str = os.getenv("USER_ID", "")

# Stake limits from spec
MIN_STAKE: float = 1.00
MAX_STAKE: float = 100.00
