from database import (
    save_lead as db_save_lead,
    get_lead_by_email,
    update_pipeline_stage,
    increase_lead_score,
    update_lead_signals
)

# ===============================
# BASE LEAD SCORING
# ===============================

def calculate_base_score(user_type):
    if user_type == "School":
        return 40
    elif user_type == "Parent":
        return 20
    return 10


# ===============================
# INTELLIGENT SIGNAL SCORING
# ===============================

def calculate_signal_score(signals):
    """
    Score based on structured AI extracted signals.
    """
    if not signals:
        return 0

    score = 0

    if signals.get("grade"):
        score += 10

    if signals.get("program_interest"):
        score += 15

    if signals.get("urgency") == "High":
        score += 20
    elif signals.get("urgency") == "Medium":
        score += 10

    if signals.get("intent") == "Demo":
        score += 25
    elif signals.get("intent") == "Partnership":
        score += 30
    elif signals.get("intent") == "Enrollment":
        score += 20

    if signals.get("budget_signal") == "Premium":
        score += 10
    elif signals.get("budget_signal") == "Sensitive":
        score -= 5

    return score


# ===============================
# PIPELINE STAGE LOGIC
# ===============================

def determine_pipeline_stage(total_score):
    if total_score >= 90:
        return "Hot"
    elif total_score >= 60:
        return "Qualified"
    elif total_score >= 30:
        return "Warm"
    else:
        return "New"


# ===============================
# SAVE / UPDATE LEAD
# ===============================

def save_lead(name, email, phone, user_type,
              intent=None,
              grade=None,
              interest=None):

    existing = get_lead_by_email(email)

    base_score = calculate_base_score(user_type)

    if existing:
        # Existing Lead
        lead_id = existing[0]
        current_score = existing[11]  # lead_score index after schema upgrade

        increase_lead_score(lead_id, base_score)

        new_total = current_score + base_score

        new_stage = determine_pipeline_stage(new_total)
        update_pipeline_stage(lead_id, new_stage)

        return new_total

    # New Lead
    db_save_lead(
        name=name,
        email=email,
        phone=phone,
        user_type=user_type,
        grade=grade,
        interest=interest,
        lead_score=base_score
    )

    lead = get_lead_by_email(email)

    stage = determine_pipeline_stage(base_score)
    update_pipeline_stage(lead[0], stage)

    return base_score


# ===============================
# INTELLIGENT SIGNAL UPDATE
# ===============================

def apply_ai_signals(lead_id, signals):
    """
    Apply structured AI extracted signals to CRM and scoring.
    """

    if not signals:
        return

    # Update CRM fields
    update_lead_signals(lead_id, signals)

    # Score based on signals
    signal_score = calculate_signal_score(signals)

    if signal_score != 0:
        increase_lead_score(lead_id, signal_score)

        # Fetch updated lead to re-evaluate stage
        from database import get_lead_by_email
        # We don’t have email here, so better to re-fetch by id in future.
        # For now, stage update handled next chat cycle.


