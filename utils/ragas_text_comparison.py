from ragas.dataset_schema import SingleTurnSample
from ragas.metrics._factual_correctness import FactualCorrectness
from ragas.metrics import SemanticSimilarity
from utils.llm import get_evaluator_llm, get_evaluator_embeddings
import asyncio
from enum import Enum
from typing import Union

class ComparisonType(Enum):
    FACTUAL_CORRECTNESS = "factual_correctness"
    SEMANTIC_SIMILARITY = "semantic_similarity"

LABEL_FORMAT = {
    ComparisonType.FACTUAL_CORRECTNESS.value: "Correção Factual",
    ComparisonType.SEMANTIC_SIMILARITY.value: "Similaridade Semântica"
}

async def compare_texts(
    response, 
    reference,
    comparison_type: Union[ComparisonType, str] = ComparisonType.FACTUAL_CORRECTNESS,
    mode=None,
    atomicity=None,
    model="gpt-4o-mini", 
    base_url="https://api.openai.com/v1"
):
    # Convert string to enum if needed
    if isinstance(comparison_type, str):
        comparison_type = ComparisonType(comparison_type)
    
    sample_data = {
        "response": response,
        "reference": reference,
        "mode": mode,
        "atomicity": atomicity
    }
    sample = SingleTurnSample(**sample_data)

    # Select scorer based on comparison type
    if comparison_type == ComparisonType.FACTUAL_CORRECTNESS:
        scorer = FactualCorrectness(llm=get_evaluator_llm(model, base_url))
    elif comparison_type == ComparisonType.SEMANTIC_SIMILARITY:
        scorer = SemanticSimilarity(embeddings=get_evaluator_embeddings())
    else:
        raise ValueError(f"Unsupported comparison type: {comparison_type}")
    
    result = await scorer.single_turn_ascore(sample)
    return result

def compare_texts_sync(
    response, 
    reference,
    comparison_type: Union[ComparisonType, str] = ComparisonType.FACTUAL_CORRECTNESS,
    mode=None,
    atomicity=None,
    model="gpt-4o-mini", 
    base_url="https://api.openai.com/v1"
):
    return asyncio.run(compare_texts(
        response, 
        reference,
        comparison_type=comparison_type,
        mode=mode,
        atomicity=atomicity,
        model=model, 
        base_url=base_url
    ))