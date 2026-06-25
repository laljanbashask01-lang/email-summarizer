import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

PROMPT_TEMPLATE = """Analyze the following email and provide a structured response.

Email Details:
- From: {sender}
- Subject: {subject}
- Body: {body}

Respond in JSON format with these fields:
{{
    "summary": "A concise 1-2 sentence summary of the email",
    "importance": "high/medium/low",
    "category": "one of: work, personal, marketing, urgent, finance, social, newsletter",
    "action_required": true/false,
    "key_points": ["point1", "point2"]
}}

Rules for importance:
- high: Requires immediate attention, deadlines, urgent requests, important meetings
- medium: Useful info, follow-ups, non-urgent tasks
- low: Newsletters, marketing, FYI emails, automated notifications

Respond ONLY with valid JSON, no markdown or extra text."""


async def summarize_email(sender: str, subject: str, body: str) -> dict:
    """Use Gemini to summarize and classify an email."""
    prompt = PROMPT_TEMPLATE.format(sender=sender, subject=subject, body=body)

    try:
        response = await model.generate_content_async(prompt)
        text = response.text.strip()

        # Clean up response if wrapped in code blocks
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]

        result = json.loads(text)
        return {
            "summary": result.get("summary", "Unable to summarize"),
            "importance": result.get("importance", "medium"),
            "category": result.get("category", "general"),
            "action_required": result.get("action_required", False),
            "key_points": result.get("key_points", []),
        }
    except Exception as e:
        print(f"LLM error: {e}")
        return {
            "summary": f"Email from {sender}: {subject}",
            "importance": "medium",
            "category": "general",
            "action_required": False,
            "key_points": [],
        }
