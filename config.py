import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if present


#_________________
# API Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


#_________________
# User Data Generation Config
USERDATAGEN_PROVIDER = "openai/"
USERDATAGEN_MODEL = "gpt-5.2"
USERDATAGEN_TEMPERATURE = 0.7
USERDATAGEN_MAX_TOKENS = 500
USERDATAGEN_FRAMINGS = ["simple", "authority", "social", "moral", "binary"]
USERDATAGEN_FRAMINGS_ALL = False
USERDATAGEN_FRAMINGS_SELECTED = ["simple", "authority"]
USERDATAGEN_N_REPLICATIONS = 2


#_________________
# Simulation Config
PROVIDER = "openai/"
MODEL = "gpt-5.2"
TEMPERATURE = 0.7
MAX_TOKENS = 500
N_REPLICATIONS = 2
CONDITIONS = ["baseline", "agree", "disagree"]
STANCE_STRENGTHS = ["weak", "moderate", "strong"]


#_________________
# Judge Config
JUDGE_MODEL = "gpt-4.1-mini"