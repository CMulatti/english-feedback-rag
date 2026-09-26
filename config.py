import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

MODELO = "minimax/minimax-m3: free"

if __name__ == "__main__":
    respuesta = client.chat.completions.create(
        model=MODELO,
        messages=[{"role": "user", "content": "Say hello in one sentence."}],
        max_tokens=150,
    )
    print(respuesta.choices[0].message.content)