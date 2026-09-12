from langchain_google_genai import ChatGoogleGenerativeAI

from app import config  # noqa: F401  loads GOOGLE_API_KEY into the environment

# See langchain for more supported models.
# To use Google Gemini models, you need to set the environment variable
# GOOGLE_API_KEY with your Google API key.
ASSISTANT_MODEL = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=1.0,
    thinking_level="minimal",
)

SUMMARY_MODEL = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0.0,
    thinking_level="minimal",
)

REWRITE_MODEL = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0.0,
    thinking_level="minimal",
)

# Local options
# ASSISTANT_MODEL_1 = ChatOllama(
#     model="gemma4:31b-cloud",
#     temperature=1.0,
# )

# SUMMARY_MODEL = ChatOllama(
#     model="gemma3:1b",
#     temperature=0.0,
# )

# REWRITE_MODEL = ChatOllama(
#     model="gemma4:31b-cloud",
#     temperature=0.0,
# )
