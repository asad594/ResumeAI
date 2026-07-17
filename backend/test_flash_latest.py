import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")

model = "gemini-flash-latest"
print(f"Testing model: {model}")
client = OpenAI(api_key=key, base_url=base_url)
start_time = time.time()
try:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
            {"role": "user", "content": "Return a JSON object with a key 'message' containing 'Hello'"}
        ],
        response_format={"type": "json_object"},
        temperature=0.3
    )
    elapsed = time.time() - start_time
    content = response.choices[0].message.content
    print(f"Success in {elapsed:.2f}s! Response: {content.strip()}")
except Exception as e:
    elapsed = time.time() - start_time
    print(f"Failed in {elapsed:.2f}s! Error: {e}")
