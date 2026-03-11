import sys
from pathlib import Path

# Ensure project root is on path (required for Vercel serverless)
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from flask import Flask, request, jsonify

from langgraph.graph import StateGraph, END

from Model.state import AssignmentState
from Nodes.code_analyser import analyze_code
from Nodes.evaluate_answer import evaluate_answer
from Nodes.repo_fetcher import fetch_repo
from Nodes.score_assignment import score_assignment

graph = StateGraph(AssignmentState)

graph.add_node("fetch_repo", fetch_repo)
graph.add_node("analyze_code", analyze_code)
graph.add_node("evaluate", evaluate_answer)
graph.add_node("score", score_assignment)

graph.set_entry_point("fetch_repo")

graph.add_edge("fetch_repo", "analyze_code")
graph.add_edge("analyze_code", "evaluate")
graph.add_edge("evaluate", "score")
graph.add_edge("score", END)

evaluation_workflow = graph.compile()

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify({
        "service": "Assignment Evaluator API",
        "docs": "POST /evaluate with JSON body: {\"repo_url\": \"https://github.com/...\"}",
    }), 200


@app.route("/evaluate", methods=["POST"])
def evaluate():
    from Model.llm import llm
    if llm is None:
        return jsonify({
            "error": "GROQ_API_KEY is not set. Add it in Vercel Project Settings → Environment Variables.",
        }), 503

    data = request.get_json(silent=True) or {}
    repo_url = data.get("repo_url") or data.get("repo")

    if not repo_url:
        return jsonify({"error": "Missing repo_url or repo in request body"}), 400

    try:
        result = evaluation_workflow.invoke({"repo_url": repo_url})
        response = {k: v for k, v in result.items() if k != "code"}
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)