from utils.provider import LLMProvider
import os
from typing import Optional

# Instância global
eval_llm = LLMProvider(api_key=os.getenv("OPENAI_API_KEY", "None"))

def update_eval_llm(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None
) -> None:
    """Atualiza a instância global eval_llm"""
    config = {}
    if api_key is not None:
        config['api_key'] = api_key
    if model is not None:
        config['model'] = model
    if base_url is not None:
        config['base_url'] = base_url
    
    if config:
        eval_llm.configure(**config)