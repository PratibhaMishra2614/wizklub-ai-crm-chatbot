import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
import streamlit as st
from google import genai
from prompts import (
    BASE_SYSTEM_PROMPT,
    PARENT_INSTRUCTION,
    SCHOOL_INSTRUCTION
)

from database import (
    get_bookings_by_lead,
    update_lead_signals,
    get_lead_by_email
)

from lead_manager import apply_ai_signals
from ai_extractor import extract_lead_signals

# Load local .env (for local development)
import streamlit as st
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

# If running on Streamlit Cloud
if not api_key:
    api_key = st.secrets.get("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)


embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


# ===============================
# VECTOR STORE
# ===============================

def load_vector_store():
    index = faiss.read_index("vector_store/faiss_index/index.faiss")
    chunks = np.load("vector_store/faiss_index/chunks.npy", allow_pickle=True)
    return index, chunks


# ===============================
# USER CLASSIFICATION
# ===============================

def classify_user_type(message):
    message = message.lower()

    if any(word in message for word in ["school", "principal", "curriculum", "partnership"]):
        return "School"

    if any(word in message for word in ["child", "son", "daughter", "parent", "class"]):
        return "Parent"

    return None


# ===============================
# RETRIEVAL (RAG)
# ===============================

def retrieve_chunks(query, index, chunks, k=3):
    query_vector = embedding_model.encode([query])
    distances, indices = index.search(np.array(query_vector), k)
    return [chunks[i] for i in indices[0]]


# ===============================
# MEMORY FORMATTER
# ===============================

def format_chat_history(chat_history, max_turns=5):
    recent_history = chat_history[-max_turns * 2:]
    formatted = ""

    for role, message in recent_history:
        if role == "user":
            formatted += f"User: {message}\n"
        else:
            formatted += f"Assistant: {message}\n"

    return formatted


# ===============================
# CRM CONTEXT BUILDER
# ===============================

def build_crm_context(crm_data):

    if not crm_data:
        return ""

    # Updated schema indexes:
    # 0 id
    # 1 name
    # 2 email
    # 3 phone
    # 4 user_type
    # 5 grade
    # 6 interest
    # 7 urgency
    # 8 program_interest
    # 9 budget_signal
    # 10 extracted_intent
    # 11 lead_score
    # 12 pipeline_stage
    # 13 created_at

    lead_id = crm_data[0]
    bookings = get_bookings_by_lead(lead_id)

    booking_info = ""
    if bookings:
        booking_info = "Existing Bookings:\n"
        for b in bookings:
            booking_info += f"- {b[0]} at {b[1]} ({b[2]}) - {b[3]}\n"

    return f"""
Known CRM Information:
Name: {crm_data[1]}
Email: {crm_data[2]}
User Type: {crm_data[4]}
Grade: {crm_data[5]}
Program Interest: {crm_data[8]}
Urgency: {crm_data[7]}
Budget Signal: {crm_data[9]}
Intent: {crm_data[10]}
Lead Score: {crm_data[11]}
Pipeline Stage: {crm_data[12]}

{booking_info}

Use this information to personalize responses.
"""


# ===============================
# SALES STRATEGY ENGINE
# ===============================

def build_sales_guidance(crm_data):

    if not crm_data:
        return ""

    lead_score = crm_data[11]
    stage = crm_data[12]

    guidance = ""

    if stage == "New":
        guidance = "Qualify the lead and encourage demo booking."

    elif stage == "Warm":
        guidance = "Push toward demo booking."

    elif stage == "Qualified":
        guidance = "Encourage enrollment or close conversion."

    elif stage == "Hot":
        guidance = "Treat as high-priority and drive immediate action."

    return f"Sales Strategy Guidance: {guidance}"


# ===============================
# RESPONSE GENERATOR
# ===============================

def generate_response(query, context_chunks, chat_history, user_type=None, crm_data=None):

    context = "\n\n".join(context_chunks)
    conversation_memory = format_chat_history(chat_history)

    # ===============================
    # STRUCTURED AI SIGNAL EXTRACTION
    # ===============================

    if crm_data:
        signals = extract_lead_signals(query)

        if signals:
            lead_id = crm_data[0]

            # Update CRM fields
            update_lead_signals(lead_id, signals)

            # Apply intelligent scoring
            apply_ai_signals(lead_id, signals)

            # Refresh CRM data after update
            crm_data = get_lead_by_email(crm_data[2])

    crm_context = build_crm_context(crm_data)
    sales_guidance = build_sales_guidance(crm_data)

    role_instruction = ""
    if user_type == "Parent":
        role_instruction = PARENT_INSTRUCTION
    elif user_type == "School":
        role_instruction = SCHOOL_INSTRUCTION

    final_prompt = f"""
{BASE_SYSTEM_PROMPT}

{role_instruction}

{crm_context}

{sales_guidance}

Conversation so far:
{conversation_memory}

Relevant Knowledge:
{context}

Current User Question:
{query}

Instructions:
- Personalize using known CRM information.
- If signals are missing (grade, urgency, interest), ask smart follow-up questions.
- Suggest next best action.
- Keep tone professional, persuasive, and friendly.
"""

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=final_prompt
    )

    return response.text
