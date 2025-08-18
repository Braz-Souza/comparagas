from ragas.dataset_schema import SingleTurnSample
from ragas.metrics._factual_correctness import FactualCorrectness
from utils.llm import get_evaluator_llm
import asyncio

async def compare_texts(
    response, 
    reference, 
    mode=None,
    atomicity=None,
    model="gpt-4o-mini", 
    base_url="https://api.openai.com/v1"
):
    sample_data = {
        "response": response,
        "reference": reference,
        "mode": mode,
        "atomicity": atomicity
    }
    sample = SingleTurnSample(**sample_data)

    scorer = FactualCorrectness(llm=get_evaluator_llm(model, base_url))
    result = await scorer.single_turn_ascore(sample)
    return result

def compare_texts_sync(
    response, 
    reference, 
    mode=None,
    atomicity=None,
    model="gpt-4o-mini", 
    base_url="https://api.openai.com/v1"
):
    return asyncio.run(compare_texts(
        response, 
        reference, 
        mode=mode,
        atomicity=atomicity,
        model=model, 
        base_url=base_url
    ))