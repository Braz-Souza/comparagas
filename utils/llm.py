import os
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

def get_evaluator_llm(model="gpt-4o-mini", base_url="https://api.openai.com/v1"):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY não encontrada nas variáveis de ambiente")
    return LangchainLLMWrapper(ChatOpenAI(
        model=model, 
        api_key=api_key,
        base_url=base_url
    ))

def get_evaluator_embeddings():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY não encontrada nas variáveis de ambiente")
    return LangchainEmbeddingsWrapper(OpenAIEmbeddings(api_key=api_key))
