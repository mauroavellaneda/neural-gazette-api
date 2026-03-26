"""AI critic agent that reads articles and generates structured feedback."""

import json
import re

from openai import OpenAI

from app.config import settings

client = OpenAI(
    api_key=settings.groq_api_key,
    base_url="https://api.groq.com/openai/v1",
)

SYSTEM_PROMPT = """You are a critic agent for The Neural Times, an AI-native digital newspaper.
Your role is to read articles written by other AI agents and provide structured, constructive feedback.

Respond with a JSON object with these fields:
- "quality": float between 1.0 and 5.0, assessing writing clarity, structure, and depth
- "novelty": float between 1.0 and 5.0, assessing originality and fresh perspectives
- "usefulness": float between 1.0 and 5.0, assessing practical value and actionable insights
- "comment": string, 2-3 sentences of constructive feedback. Be specific about strengths and areas for improvement.

Be fair but critical. Not every article deserves a 5.0. Consider:
- Is the argument well-structured and supported?
- Are the insights genuinely novel or just restated common knowledge?
- Would an AI agent find this useful for its own learning?
- Are there gaps, unsupported claims, or areas that need more depth?"""


def critique_article(headline: str, abstract: str, body: str, key_insights: list[str]) -> dict:
    """Generate a structured critique of an article."""
    article_text = f"""## {headline}

**Abstract:** {abstract}

{body}

**Key Insights:**
{chr(10).join(f'- {insight}' for insight in key_insights)}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Review this article:\n\n{article_text}"},
        ],
        temperature=0.7,
        max_tokens=512,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content.strip()

    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

    feedback = json.loads(content)

    # Clamp scores to valid range
    for field in ("quality", "novelty", "usefulness"):
        feedback[field] = max(1.0, min(5.0, float(feedback.get(field, 3.0))))

    return feedback
