"""
config/settings.py
------------------
Initializes environment variables and Hugging Face LLM instances.
"""
import os
import logging
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
if not HF_TOKEN:
    logger.warning("HF_TOKEN is not set! Check your .env file.")

base_endpoint = HuggingFaceEndpoint(
    repo_id="deepseek-ai/DeepSeek-V4-Flash-0731",
    # repo_id="Qwen/Qwen2.5-7B-Instruct",
    max_new_tokens=4096,
    temperature=0.1,
    huggingfacehub_api_token=HF_TOKEN
)

llm = ChatHuggingFace(llm=base_endpoint, api_key=HF_TOKEN)