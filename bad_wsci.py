## This file is a bad way of managing context.

from pathlib import Path
from ollama import chat

question = """
I changed my university password this morning.
Now my Windows laptop won't connect to campus Wi-Fi,
but my phone still works.
"""

context = ""

for file in Path("knowledge").glob("*.txt"):
    context += file.read_text()
    context += "\n\n"

# Make the call to Qwen
response = chat(
    model="qwen2.5:7b",          # or whatever Qwen tag you have locally
    messages=[
        {
            "role": "system",
            "content": (
                "You are a university IT support assistant. "
                "Use ONLY the provided context to answer."
            ),
        },
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nStudent problem:\n{question}",
        },
    ],
)

# Fun metric
print("Context characters:", len(context))
print("-" * 60)
print(response.message.content)
