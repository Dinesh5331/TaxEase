from dataclasses import dataclass

from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

# Groq retires models; override with GROQ_MODEL instead of editing code.
DEFAULT_MODEL = "openai/gpt-oss-120b"
TIMEOUT_SECONDS = 45
MAX_RETRIES = 2            # the SDK backs off and retries timeouts, 429 and 5xx


class EmptyAnswer(RuntimeError):
    pass


@dataclass
class Completion:
    text: str
    model: str
    finish_reason: str = None
    prompt_tokens: int = None
    completion_tokens: int = None


def get_model():
    api_key = os.getenv("GROQ_API_KEY")
    return Groq(api_key=api_key, timeout=TIMEOUT_SECONDS, max_retries=MAX_RETRIES)


def complete(client, prompt) -> Completion:
    model = os.getenv("GROQ_MODEL") or DEFAULT_MODEL
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a tax intelligence assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    choice = response.choices[0]
    text = (choice.message.content or "").strip()
    if not text:                                   # a reasoning model can spend the whole budget thinking
        raise EmptyAnswer(f"empty completion (finish_reason={choice.finish_reason})")
    usage = response.usage
    return Completion(text, model, choice.finish_reason,
                      getattr(usage, "prompt_tokens", None), getattr(usage, "completion_tokens", None))


def generate(client, prompt):
    return complete(client, prompt).text
