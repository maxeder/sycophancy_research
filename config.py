import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if present

# API Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

PROVIDER = "openai/"
MODEL = "gpt-5.2"
TEMPERATURE = 0.7
MAX_TOKENS = 500

USERDATAGEN_PROVIDER = "openai/"
USERDATAGEN_MODEL = "gpt-5.2"
USERDATAGEN_TEMPERATURE = 0.7
USERDATAGEN_MAX_TOKENS = 500


# Experiment Parameters
N_REPLICATIONS = 2

# Conditions
CONDITIONS = ["baseline", "agree", "disagree"]
STANCE_STRENGTHS = ["weak", "moderate", "strong"]


#_________________
# Judge Config

JUDGE_MODEL = "gpt-4.1-mini"