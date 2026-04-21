"""
ChestGuard NeuralScan — Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload

# Model config
MODEL_WEIGHTS = "densenet121-res224-all"
IMAGE_SIZE = 224

# LLM config
LLM_MODEL = "llama-3.1-8b-instant"
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 2048
