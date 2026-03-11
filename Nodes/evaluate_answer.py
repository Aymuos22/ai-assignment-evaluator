from Model.llm import llm


def evaluate_answer(state):

    analysis = state["analysis"]

    prompt = f"""
You are a strict programming instructor.

Based on this analysis of a student's code:

{analysis}

Provide:
1. Strengths
2. Weaknesses
3. Missing features
"""

    feedback = llm.invoke(prompt).content

    return {"feedback": feedback}