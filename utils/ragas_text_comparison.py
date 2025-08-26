from ragas.dataset_schema import SingleTurnSample
from ragas.metrics._factual_correctness import FactualCorrectness
from ragas.metrics import SemanticSimilarity
from ragas.metrics._string import NonLLMStringSimilarity
from utils.llm import eval_llm, update_eval_llm
import asyncio
import os
from enum import Enum
from typing import Union

class ComparisonType(Enum):
    FACTUAL_CORRECTNESS = "factual_correctness"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    NON_LLM_STRING_SIMILARITY = "non_llm_string_similarity"

LABEL_FORMAT = {
    ComparisonType.FACTUAL_CORRECTNESS.value: "Correção Factual",
    ComparisonType.SEMANTIC_SIMILARITY.value: "Similaridade Semântica",
    ComparisonType.NON_LLM_STRING_SIMILARITY.value: "Similaridade de String Não-LLM"
}

LABEL_OPTIONS = [
    ComparisonType.FACTUAL_CORRECTNESS.value,
    ComparisonType.SEMANTIC_SIMILARITY.value,
    ComparisonType.NON_LLM_STRING_SIMILARITY.value,
]

def _get_scorer(comparison_type: ComparisonType):
    """Factory para criar scorer baseado no tipo de comparação"""
    if comparison_type == ComparisonType.FACTUAL_CORRECTNESS:
        return FactualCorrectness(llm=eval_llm.get_llm_evaluator())
    elif comparison_type == ComparisonType.SEMANTIC_SIMILARITY:
        try:
            embeddings = eval_llm.get_evaluator_embeddings()
            return SemanticSimilarity(embeddings=embeddings)
        except Exception as e:
            # Se o provedor não suporta embeddings, lança erro mais específico
            if "'str' object has no attribute 'data'" in str(e):
                raise ValueError("O provedor/modelo escolhido não possui método de embedding necessário para Similaridade Semântica")
            else:
                raise ValueError(f"Erro ao configurar embeddings: {str(e)}")
    elif comparison_type == ComparisonType.NON_LLM_STRING_SIMILARITY:
        return NonLLMStringSimilarity()
    else:
        raise ValueError(f"Tipo de comparação não suportado: {comparison_type}")

async def compare_texts(
    response: str, 
    reference: str,
    comparison_type: Union[ComparisonType, str] = ComparisonType.FACTUAL_CORRECTNESS,
    mode: str = None,
    atomicity: str = None,
    model: str = "gpt-4o-mini", 
    base_url: str = "https://api.openai.com/v1"
) -> float:
    """Compara textos usando RAGAS"""
    # Normalizar tipo de comparação
    if isinstance(comparison_type, str):
        comparison_type = ComparisonType(comparison_type)
    
    # Atualizar configuração
    update_eval_llm(
        api_key=os.getenv("OPENAI_API_KEY", "None"),
        model=model,
        base_url=base_url
    )
    
    try:
        # Criar sample e scorer
        sample = SingleTurnSample(
            response=response,
            reference=reference,
            mode=mode,
            atomicity=atomicity
        )
        
        scorer = _get_scorer(comparison_type)
        return await scorer.single_turn_ascore(sample)
    
    except Exception as e:
        # Capturar erro específico de embedding
        if "'str' object has no attribute 'data'" in str(e):
            raise ValueError("Erro durante avaliação: 'str' object has no attribute 'data' - A opção escolhida não tem método de embedding")
        else:
            raise

def compare_texts_sync(
    response: str, 
    reference: str,
    comparison_type: Union[ComparisonType, str] = ComparisonType.FACTUAL_CORRECTNESS,
    mode: str = None,
    atomicity: str = None,
    model: str = "gpt-4o-mini", 
    base_url: str = "https://api.openai.com/v1"
) -> float:
    """Versão síncrona de compare_texts"""
    try:
        return asyncio.run(compare_texts(
            response, reference, comparison_type, mode, atomicity, model, base_url
        ))
    except Exception as e:
        # Capturar erro específico de embedding
        if "'str' object has no attribute 'data'" in str(e):
            raise ValueError("Erro durante avaliação: 'str' object has no attribute 'data' - A opção escolhida não tem método de embedding")
        else:
            raise