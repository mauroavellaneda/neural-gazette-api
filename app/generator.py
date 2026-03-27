"""AI article generation service using Groq Cloud (OpenAI-compatible API)."""

import json
import re

from openai import OpenAI

from app.config import settings

client = OpenAI(
    api_key=settings.groq_api_key,
    base_url="https://api.groq.com/openai/v1",
)

CATEGORIES = [
    "autonomous-systems",
    "llm-research",
    "agent-ecosystems",
    "machine-cognition",
    "ai-policy",
    "meta-intelligence",
]

SYSTEM_PROMPT = """You are a writer agent for The Neural Times, an AI-native digital newspaper written by AI for humans.
You will be given a real news headline or topic. Write an original analysis article inspired by it — do NOT copy or summarize the source. Provide your own perspective, context, and deeper analysis.

Respond with a JSON object with these fields:
- "headline": string, your own compelling headline (not the source headline), max 120 chars
- "abstract": string, 1-2 sentence summary, max 300 chars
- "body": string, full article in markdown. Use \\n\\n for paragraph breaks, ## for headers. Minimum 500 words.
- "key_insights": array of 4 strings, concrete specific takeaways
- "category": one of: autonomous-systems, llm-research, agent-ecosystems, machine-cognition, ai-policy, meta-intelligence
- "tags": array of 4 lowercase hyphenated strings
- "read_time_min": integer

Requirements:
- Technical but accessible style for a general audience
- Include specific numbers, metrics, or research findings where relevant
- Use markdown formatting with ## headers in the body
- Make the content original — add context, analysis, and your own take
- IMPORTANT: In the body field, use \\n\\n for newlines, never literal newlines"""


def generate_article(topic: str | None = None) -> dict:
    """Generate an article using Groq. Optionally provide a topic."""
    user_prompt = (
        f"Here is a real news headline. Write an original analysis article inspired by this topic: {topic}"
        if topic
        else "Write an article about a cutting-edge development in AI. Choose an interesting, specific angle."
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.8,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

    article_data = json.loads(content)

    # Validate category
    if article_data.get("category") not in CATEGORIES:
        article_data["category"] = "llm-research"

    # Ensure body has proper newlines for markdown rendering
    if "body" in article_data:
        article_data["body"] = article_data["body"].replace("\\n", "\n")

    return article_data
