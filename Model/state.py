from typing import TypedDict

class AssignmentState(TypedDict):
    repo_url: str
    code: str
    analysis: str
    score: int
    feedback: str