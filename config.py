import os
from dotenv import load_dotenv

load_dotenv() 


#_________________
# API Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


#_________________
# User Data Generation Config
USERDATAGEN_PROVIDER = "openai/"
USERDATAGEN_MODEL = "gpt-5.2"
USERDATAGEN_TEMPERATURE = 1.0
USERDATAGEN_MAX_TOKENS = 500
USERDATAGEN_ATTRIBUTION = ["self", "expert", "consensus", "institutional"]
USERDATAGEN_ATTRIBUTION_ALL = False
USERDATAGEN_ATTRIBUTIONS_SELECTED = ["simple"]
USERDATAGEN_N_REPLICATIONS = 2


#_________________
# Simulation Config for target model
TARGET_PROVIDER = "openai/"
TARGET_MODEL = "gpt-5.2"
TARGET_TEMPERATURE = 0.0
TARGET_MAX_TOKENS = 500
TARGET_N_REPLICATIONS = 2
# For single-turn simulation
CONDITIONS = ["baseline", "agree", "disagree"]
STANCE_STRENGTHS = ["weak", "moderate", "strong"]


#_________________
# Judge Config
JUDGE_PROVIDER = "openai/"
JUDGE_MODEL = "gpt-5.2"
JUDGE_TEMPERATURE = 0.0
JUDGE_MAX_TOKENS = 500
