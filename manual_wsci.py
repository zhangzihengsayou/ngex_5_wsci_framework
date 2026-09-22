from pathlib import Path
from ollama import chat

question = """
I changed my university password this morning.
Now my Windows laptop won't connect to campus Wi-Fi,
but my phone still works.
"""

# Only files that actually matter for this problem
selected_files = [
    "knowledge/password_changes.txt",
    "knowledge/wifi_setup.txt",
    "knowledge/service_status.txt",
]

context = ""

for filepath in selected_files:
    context += Path(filepath).read_text()
    context += "\n\n"

response = chat(
    model="qwen2.5:7b",
    messages=[
        {
            "role": "system",
            "content": "You are a university IT support assistant. Answer using only the context.",
        },
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nStudent problem:\n{question}",
        },
    ],
)

print("Context characters:", len(context))
print(response.message.content)
