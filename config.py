import os
from dotenv import load_dotenv

load_dotenv()

# API Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4.1-mini"

# TEMPERATURE = 0.7
MAX_TOKENS = 500

# Experiment Parameters
N_REPLICATIONS = 2

# Conditions
CONDITIONS = ["baseline", "agree", "disagree"]
STANCE_STRENGTHS = ["weak", "moderate", "strong"]


#_________________
# Judge Config

JUDGE_MODEL = "gpt-4.1-mini"