import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langfuse import Langfuse
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# def get_llm():
#     return AzureChatOpenAI(
#         openai_api_key=os.getenv("AOAI_API_KEY"),
#         azure_endpoint=os.getenv("AOAI_ENDPOINT"),
#         azure_deployment="gpt-35-turbo",  # or your deployment
#         api_version="2023-06-01-preview",  # or your api version
#         temperature=0.7,
#         streaming=True
#     )

def get_llm():
    return AzureChatOpenAI(
        openai_api_key   = os.getenv("AOAI_API_KEY"),
        azure_endpoint=os.getenv("AOAI_ENDPOINT"),
        api_version = os.getenv("AOAI_API_VERSION"),
        deployment_name  = os.getenv("AOAI_DEPLOY_GPT4O_MINI"),
        temperature      = 0.7,
        streaming=True
    )

def get_embeddings():
    return AzureOpenAIEmbeddings(
        model=os.getenv("AOAI_DEPLOY_EMBED_3_SMALL"),
        openai_api_version=os.getenv("AOAI_EMBED_API_VERSION"),
        api_key=os.getenv("AOAI_API_KEY"),
        azure_endpoint=os.getenv("AOAI_ENDPOINT"),
    )


def get_langfuse():
    return Langfuse(
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        host=os.getenv("LANGFUSE_HOST"),
    )


langfuse = get_langfuse()
