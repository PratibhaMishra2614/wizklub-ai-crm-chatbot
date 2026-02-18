def recommend_action(lead_score, stage):

    if stage == "New":
        return "Encourage demo booking."

    if stage == "Qualified":
        return "Push toward demo scheduling."

    if stage == "Booked":
        return "Send reminder and preparation info."

    if lead_score >= 80:
        return "High priority lead — immediate counselor follow-up."

    return "Maintain engagement."
