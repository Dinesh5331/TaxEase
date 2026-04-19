from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()


def get_model():
    api_key = os.getenv("GROQ_API_KEY")
    return Groq(api_key=api_key)


def generate(client, prompt):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a tax intelligence assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content