from Model.llm import llm


def analyze_code(state):

    code = state["code"]

    prompt = f"""
You are a senior software engineer.

Analyze the following student assignment code.

Explain:
1. What the code does
2. Key ML techniques used
3. Whether it solves the assignment

Code:
{code}
"""

    analysis = llm.invoke(prompt).content

    return {"analysis": analysis}