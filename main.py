# main.py
import os
import json
import re
from anthropic import Anthropic
from prompts import WRITER_SYSTEM, CRITIC_SYSTEM
from executor import run_code

from dotenv import load_dotenv
load_dotenv()

client = Anthropic()
MODEL = "claude-opus-4-7"  # or whatever current model you prefer
MAX_ITERATIONS = 5

def extract_code(text: str) -> str:
    """Pull the first python code block out of the writer's output."""
    match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()

def call_writer(spec: str, previous_code: str = None, feedback: dict = None) -> str:
    if previous_code is None:
        user_msg = f"Specification:\n\n{spec}"
    else:
        user_msg = (
            f"Specification:\n\n{spec}\n\n"
            f"Previous version:\n```python\n{previous_code}\n```\n\n"
            f"Critic feedback:\n{json.dumps(feedback, indent=2)}\n\n"
            f"Revise the code to address each blocking issue."
        )
    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=WRITER_SYSTEM,
        messages=[{"role": "user", "content": user_msg}]
    )
    return extract_code(response.content[0].text)

def call_critic(spec: str, code: str) -> dict:
    # Have the critic run the code first
    execution = run_code(code)
    user_msg = (
        f"Specification:\n\n{spec}\n\n"
        f"Code to review:\n```python\n{code}\n```\n\n"
        f"Execution result:\n{json.dumps(execution, indent=2)}\n\n"
        f"Review the code based on the spec and the execution result. "
        f"Output strict JSON as described in your instructions."
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=CRITIC_SYSTEM,
        messages=[{"role": "user", "content": user_msg}]
    )
    text = response.content[0].text
    # Strip any markdown fences around the JSON
    text = re.sub(r"^```(?:json)?\n?", "", text.strip())
    text = re.sub(r"\n?```$", "", text)
    return json.loads(text)

def writer_critic_loop(spec: str) -> tuple[str, list]:
    code = None
    feedback = None
    history = []
    for iteration in range(MAX_ITERATIONS):
        print(f"\n--- Iteration {iteration + 1} ---")
        code = call_writer(spec, code, feedback)
        print(f"Writer produced {len(code)} chars of code")
        feedback = call_critic(spec, code)
        history.append({'iteration': iteration + 1, 'feedback': feedback})
        print(f"Critic verdict: {feedback['verdict']}")
        for issue in feedback.get('issues', []):
            print(f"  [{issue['severity']}] {issue['description']}")
        if feedback['verdict'] == 'APPROVED':
            return code, history
        if not any(i['severity'] == 'blocking' for i in feedback.get('issues', [])):
            return code, history  # only minor issues, ship it
    return code, history  # ran out of iterations

if __name__ == "__main__":
    spec = """
    Write a function `fetch_arxiv_papers(query: str, max_results: int = 10) -> list[dict]`
    that queries arxiv.org for papers matching the query and returns a list of dicts
    with keys: title, authors, abstract, url, published_date.
    Use the arxiv API at http://export.arxiv.org/api/query.
    Handle network errors and empty results gracefully.
    """
    final_code, history = writer_critic_loop(spec)
    with open("workspace/output.py", "w") as f:
        f.write(final_code)
    print("\n--- Final code saved to workspace/output.py ---")
    print(f"Iterations: {len(history)}")