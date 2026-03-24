import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

MODEL_NAME = "claude-haiku-4-5-20251001"

MAX_TOKENS_AGENT = 2048
MAX_TOKENS_SUPERVISOR = 3000

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "code-review-knowledge")
