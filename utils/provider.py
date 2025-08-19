from typing import Dict, Any, List
from openai import OpenAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

class LLMProvider:
    """Simplified LLM provider using OpenAI API"""
    
    def __init__(self, api_key: str = "None", model: str = "gpt-4o-mini", base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
    
    def _validate_api_key(self) -> None:
        if not self.api_key or self.api_key == "None" or not self.api_key.strip():
            raise ValueError("API Key não configurada")
    
    def get_available_models(self) -> List[str]:
        """Busca modelos disponíveis no endpoint"""
        try:
            self._validate_api_key()
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            models = client.models.list()
            return sorted([model.id for model in models.data])
        except Exception:
            return [] 
    
    def get_llm_evaluator(self) -> LangchainLLMWrapper:
        """Retorna avaliador LLM configurado"""
        self._validate_api_key()
        return LangchainLLMWrapper(ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url
        ))
    
    def get_evaluator_embeddings(self) -> LangchainEmbeddingsWrapper:
        """Retorna embeddings configurados"""
        self._validate_api_key()
        config = {"api_key": self.api_key}
        if self.base_url != "https://api.openai.com/v1":
            config["base_url"] = self.base_url
        return LangchainEmbeddingsWrapper(OpenAIEmbeddings(**config))
    
    def configure(self, **config) -> None:
        """Atualiza configurações"""
        for key in ["api_key", "model", "base_url"]:
            if key in config:
                setattr(self, key, config[key])
    
    def get_info(self) -> Dict[str, Any]:
        """Retorna informações do provedor"""
        # Determine provider name based on base URL
        provider_name = "OpenAI"
        if "openrouter.ai" in self.base_url:
            provider_name = "OpenRouter"
        elif "api.openai.com" in self.base_url:
            provider_name = "OpenAI"
        
        return {
            "provider": provider_name,
            "model": self.model,
            "base_url": self.base_url,
            "api_key_set": bool(self.api_key and self.api_key != "None" and self.api_key.strip())
        }
