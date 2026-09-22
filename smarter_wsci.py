from pathlib import Path
from ollama import chat
import json

MODEL = "qwen2.5:7b"

question = """
I changed my university password this morning.
Now my Windows laptop won't connect to campus Wi-Fi,
but my phone still works.
"""

# ---------------------------------------------------------------
# ISOLATE — build separate state artifacts for separate tasks
# ---------------------------------------------------------------
diagnostic_state = {
    "problem": question,
    "device": "Windows laptop",
    "wifi_status": "operational",
    "other_device_works": True,
    "password_changed_recently": True,
}

report_state = {
    "total_wifi_cases": 37,
    "resolved_cases": 29,
    "unresolved_cases": 8,
}

# ---------------------------------------------------------------
# SELECT — pick relevant files by keyword
# ---------------------------------------------------------------
def select_context(question: str) -> list[str]:
    """Return a list of knowledge-base files relevant to the question."""
    q = question.lower()

    rules = {
        "wifi":       "wifi_setup.txt",
        "wi-fi":      "wifi_setup.txt",
        "eduroam":    "wifi_setup.txt",
        "password":   "password_changes.txt",
        "credential": "password_changes.txt",
        "email":      "email_setup.txt",
        "vpn":        "vpn.txt",
        "print":      "printing.txt",
        "printer":    "printing.txt",
        "projector":  "classroom_projectors.txt",
        "display":    "classroom_projectors.txt",
    }

    chosen = set()
    for keyword, filename in rules.items():
        if keyword in q:
            chosen.add(f"knowledge/{filename}")

    # Always include service status for diagnostic questions
    chosen.add("knowledge/service_status.txt")

    return sorted(chosen)


selected_files = select_context(question)
print("Selected files:", selected_files)

# ---------------------------------------------------------------
# READ selected files
# ---------------------------------------------------------------
context = ""
for filepath in selected_files:
    context += Path(filepath).read_text()
    context += "\n\n"

# ---------------------------------------------------------------
# COMPRESS — let Qwen reduce the context to only what matters
# ---------------------------------------------------------------
def compress_context(context: str, question: str) -> str:
    """Return a compressed version of the context, keeping only relevant info."""
    compression_prompt = f"""You are an information compressor.

Extract ONLY the information from the context below that is relevant to
answering the student's question. Remove everything else. Keep it factual,
concise, and in bullet points.

Student question:
{question}

Full context:
{context}

Compressed context:"""

    resp = chat(
        model=MODEL,
        messages=[{"role": "user", "content": compression_prompt}],
    )
    return resp.message.content


compressed_context = compress_context(context, question)
print("Compressed context characters:", len(compressed_context))

# ---------------------------------------------------------------
# Call Qwen with the COMPRESSED context, ask for structured output
# ---------------------------------------------------------------
final_prompt = f"""You are a university IT support assistant.

Use the compressed context below to answer the student's problem.

Compressed context:
{compressed_context}

Student problem:
{question}

Respond ONLY with valid JSON in exactly this schema:
{{
  "diagnosis": "one-sentence root cause",
  "steps": ["step 1", "step 2", "step 3"],
  "confidence": "low|medium|high"
}}
"""

response = chat(
    model=MODEL,
    messages=[{"role": "user", "content": final_prompt}],
    format="json",  # Ollama enforces JSON output
)

print(response.message.content)

# ---------------------------------------------------------------
# WRITE — save structured result to state.json
# ---------------------------------------------------------------
try:
    answer = json.loads(response.message.content)
except json.JSONDecodeError:
    answer = {"raw": response.message.content}

state = {
    "diagnostic": diagnostic_state,
    "report": report_state,
    "answer": answer,
    "selected_files": selected_files,
}

with open("state.json", "w") as f:
    json.dump(state, f, indent=2)

print("\nWrote state.json")

# ---------------------------------------------------------------
# Reuse state.json — show that only the relevant slice is fed back
# ---------------------------------------------------------------
with open("state.json") as f:
    loaded_state = json.load(f)

# Pick only the slice appropriate to a follow-up diagnostic turn
followup_context = {
    "answer": loaded_state["answer"],
    "device": loaded_state["diagnostic"]["device"],
}

followup = chat(
    model=MODEL,
    messages=[
        {
            "role": "system",
            "content": "You are a university IT support assistant.",
        },
        {
            "role": "user",
            "content": (
                f"Context slice:\n{json.dumps(followup_context, indent=2)}\n\n"
                "Question: In one sentence, what should the student try first?"
            ),
        },
    ],
)

print("\nFollow-up answer:")
print(followup.message.content)
