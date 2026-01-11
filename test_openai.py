import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path("backend") / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    r = client.responses.create(
        model="gpt-4.1-mini",
        input="Say hello"
    )
    print("SUCCESS:", r.output_text)
except Exception as e:
    print("ERROR:", e)
