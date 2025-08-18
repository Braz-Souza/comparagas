import openai
from typing import List

def get_available_models(base_url: str, api_key: str) -> List[str]:
    """
    Busca os modelos disponíveis no endpoint especificado
    
    Args:
        base_url (str): URL base da API
        api_key (str): Chave da API
        
    Returns:
        List[str]: Lista dos nomes dos modelos disponíveis
    """
    try:
        client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # Busca todos os modelos disponíveis
        models = client.models.list()
        
        # Extrai apenas os nomes dos modelos e ordena
        model_names = [model.id for model in models.data]
        model_names.sort()
        
        return model_names
        
    except Exception as e:
        # Em caso de erro, retorna modelos padrão da OpenAI
        print(f"Erro ao buscar modelos: {e}")
        return ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]