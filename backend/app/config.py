import os
from pydantic_settings import BaseSettings

# Resolve paths relative to this config file
APP_DIR = os.path.dirname(os.path.abspath(__file__)) # d:\SupportBOT\backend\app
BACKEND_DIR = os.path.dirname(APP_DIR) # d:\SupportBOT\backend
PROJECT_ROOT = os.path.dirname(BACKEND_DIR) # d:\SupportBOT

class Settings(BaseSettings):
    # API Configurations
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Ollama LLM Settings
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma")
    
    # Storage Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BACKEND_DIR, 'instance', 'database.db')}")
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", os.path.join(BACKEND_DIR, "instance", "chroma_db"))
    KNOWLEDGE_BASE_DIR: str = os.getenv("KNOWLEDGE_BASE_DIR", os.path.join(PROJECT_ROOT, "knowledge_base"))
    
    # Clustering Settings
    CLUSTERING_THRESHOLD: float = 0.80  # Cosine similarity threshold for duplicate detection
    
    # Integration Placeholders
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_REPO: str = os.getenv("GITHUB_REPO", "flowzint/support-tickets")
    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")

    class Config:
        env_file = ".env"

settings = Settings()

# Ensure directories exist
os.makedirs(os.path.join(BACKEND_DIR, "instance"), exist_ok=True)
