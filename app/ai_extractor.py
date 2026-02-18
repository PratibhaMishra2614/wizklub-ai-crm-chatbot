from google import genai
from dotenv import load_dotenv
import os
import json
import re

import streamlit as st
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

# If running on Streamlit Cloud
if not api_key:
    api_key = st.secrets.get("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

# ===============================
# SAFE JSON PARSER
# ===============================

def safe_json_extract(text):
    """
    Extract JSON block safely from model output.
    """
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            return None

        json_str = match.group(0)
        return json.loads(json_str)

    except:
        return None


# ===============================
# VALUE NORMALIZATION
# ===============================

def normalize_signals(data):
    """
    Clean and normalize extracted values.
    """

    if not data:
        return None

    normalized = {
        "grade": data.get("grade"),
        "program_interest": data.get("program_interest"),
        "urgency": data.get("urgency"),
        "budget_signal": data.get("budget_signal"),
        "intent": data.get("intent")
    }

    # Normalize urgency
    if normalized["urgency"]:
        normalized["urgency"] = normalized["urgency"].capitalize()

    # Normalize budget
    if normalized["budget_signal"]:
        normalized["budget_signal"] = normalized["budget_signal"].capitalize()

    # Normalize intent
    if normalized["intent"]:
        normalized["intent"] = normalized["intent"].capitalize()

    return normalized


# ===============================
# MAIN EXTRACTION FUNCTION
# ===============================

def extract_lead_signals(text):

    prompt = f"""
You are an AI sales qualification extractor.

Extract structured lead qualification data from the message.

Return ONLY valid JSON.

Required fields:
- grade (e.g., Grade 6, Class 8)
- program_interest (Robotics, Coding, AI, Math, etc.)
- urgency (High, Medium, Low)
- budget_signal (Sensitive, Neutral, Premium)
- intent (Demo, Partnership, Exploration, Enrollment)

If not found, return null for that field.

Return format example:
{{
  "grade": null,
  "program_interest": null,
  "urgency": null,
  "budget_signal": null,
  "intent": null
}}

Message:
{text}
"""

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash-002",
            contents=prompt
        )

        raw_output = response.text.strip()

        parsed = safe_json_extract(raw_output)

        if not parsed:
            return None

        return normalize_signals(parsed)

    except Exception:
        return None
