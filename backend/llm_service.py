import os
import json
import ssl
import certifi
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Fix SSL on Windows
os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = certifi.where()
os.environ["SSL_CERT_FILE"] = certifi.where()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"), transport="rest")
model = genai.GenerativeModel("gemini-2.5-flash")

PROMPT_TEMPLATE = """You are an advanced email analyst AI. Analyze the following email thoroughly.

Email Details:
- From: {sender}
- Subject: {subject}
- Body: {body}

Respond in JSON format with ALL these fields:
{{
    "summary": "A concise 2-3 sentence summary of the email content",
    "importance": "high/medium/low",
    "category": "one of: work, personal, marketing, urgent, finance, social, newsletter, notification",
    "sentiment": "positive/negative/neutral/mixed",
    "tone": "one of: formal, informal, friendly, aggressive, urgent, promotional, threatening, appreciative",
    "spam_classification": "ham/spam/phishing",
    "spam_confidence": 0.0 to 1.0,
    "threat_level": "none/low/medium/high",
    "action_required": true/false,
    "reply_urgency": "immediate/within_24h/when_possible/no_reply_needed",
    "suggested_reply": "A brief 1-line suggested reply if action is needed, or null",
    "key_points": ["point1", "point2"],
    "emotional_cues": ["list of detected emotions"],
    "red_flags": ["any suspicious elements like fake urgency, unknown links, impersonation attempts"]
}}

Classification Rules:

IMPORTANCE:
- high: Deadlines, urgent requests, important meetings, financial alerts, security warnings
- medium: Useful info, follow-ups, non-urgent tasks, questions
- low: Newsletters, marketing, FYI, automated notifications

SENTIMENT:
- positive: Good news, appreciation, congratulations, approvals, excitement
- negative: Complaints, rejections, bad news, warnings, threats, dissatisfaction
- neutral: Informational, routine updates, no emotional charge
- mixed: Contains both positive and negative elements

SPAM CLASSIFICATION:
- ham: Legitimate email from a real person or trusted service
- spam: Unsolicited marketing, bulk email, irrelevant promotions, clickbait
- phishing: Credential theft attempts, fake urgency, suspicious links, impersonation

THREAT LEVEL:
- none: Safe, legitimate email
- low: Minor spam or unwanted marketing
- medium: Suspicious content, possible scam
- high: Clear phishing, malware, or social engineering attempt

Respond ONLY with valid JSON, no markdown or extra text."""


async def summarize_email(sender: str, subject: str, body: str) -> dict:
    """Use Gemini to summarize and classify an email."""
    prompt = PROMPT_TEMPLATE.format(sender=sender, subject=subject, body=body)

    try:
        response = model.generate_content(prompt)
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
            "sentiment": result.get("sentiment", "neutral"),
            "tone": result.get("tone", "formal"),
            "spam_classification": result.get("spam_classification", "ham"),
            "spam_confidence": result.get("spam_confidence", 0.0),
            "threat_level": result.get("threat_level", "none"),
            "action_required": result.get("action_required", False),
            "reply_urgency": result.get("reply_urgency", "no_reply_needed"),
            "suggested_reply": result.get("suggested_reply"),
            "key_points": result.get("key_points", []),
            "emotional_cues": result.get("emotional_cues", []),
            "red_flags": result.get("red_flags", []),
        }
    except Exception as e:
        print(f"LLM error: {e}")
        return {
            "summary": f"Email from {sender}: {subject}",
            "importance": "medium",
            "category": "general",
            "sentiment": "neutral",
            "tone": "formal",
            "spam_classification": "ham",
            "spam_confidence": 0.0,
            "threat_level": "none",
            "action_required": False,
            "reply_urgency": "no_reply_needed",
            "suggested_reply": None,
            "key_points": [],
            "emotional_cues": [],
            "red_flags": [],
        }
