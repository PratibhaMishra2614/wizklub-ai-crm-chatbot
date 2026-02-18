from app.database import get_all_leads

def get_pipeline_counts():
    leads = get_all_leads()
    stages = {}

    for lead in leads:
        stage = lead[8]
        stages[stage] = stages.get(stage, 0) + 1

    return stages
