from Model.llm import llm


def score_assignment(state):

    feedback = state["feedback"]

    prompt = f"""
Based on the feedback below, give a score out of 10.

Feedback:
{feedback}

Return only the number.
"""

    score = llm.invoke(prompt).content

    return {"score": int(score)}