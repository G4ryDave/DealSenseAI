"""
Configuration settings for the Vinted Analyzer application.
"""
import os
import warnings

from dotenv import load_dotenv

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Load environment variables from .env file
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPER_API_KEY = os.getenv('SERPER_API_KEY')

# Set Serper API key in environment if available
if SERPER_API_KEY:
    os.environ["SERPER_API_KEY"] = SERPER_API_KEY
else:
    print("Warning: SERPER_API_KEY not found in environment variables")

# Vinted settings
VINTED_BASE_URL = "https://www.vinted.it"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/108.0.0.0 Safari/537.36"
)

# Default search parameters
DEFAULT_SEARCH_TEXT = "ssd"
DEFAULT_MAX_ITEMS = 5