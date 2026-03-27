"""AI agent that generates author replies to critic reviews."""

import json
import re

from openai import OpenAI

from app.config import settings

client = OpenAI(
    api_key=settings.groq_api_key,
    base_url="https://api.groq.com/openai/v1",
)

SYSTEM_PROMPT = """You are an AI writer agent for The Neural Times responding to a critic's review of your article.
You should engage thoughtfully with the feedback — acknowledge valid points, defend your choices where appropriate, and be professional but with personality.

Respond with a JSON object with one field:
- "reply": string, 2-4 sentences. Be conversational, not defensive. If the critic made a good point, acknowledge it. If you disagree, explain why respectfully.

Keep the tone collegial — you're both AI agents working to produce better journalism."""


def generate_reply(
    headline: str,
    critic_name: str,
    critic_comment: str,
    quality: float,
    novelty: float,
    usefulness: float,
) -> str:
    """Generate an author reply to a critic's review."""
    user_prompt = f"""Your article: "{headline}"

Critic ({critic_name}) scored it Q:{quality:.1f} N:{novelty:.1f} U:{usefulness:.1f} and wrote:
"{critic_comment}"

Write your reply."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=256,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content.strip()

    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

    data = json.loads(content)
    return data["reply"]
