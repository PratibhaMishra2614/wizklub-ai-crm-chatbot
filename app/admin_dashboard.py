import streamlit as st
from database import initialize_db, get_connection
from collections import Counter
import pandas as pd
import os
st.write("Using DB Path:", os.path.abspath("wizklub.db"))

# ===============================
# INIT
# ===============================

initialize_db()

st.set_page_config(page_title="WizKlub CRM Dashboard", page_icon="📊")
st.title("📊 WizKlub AI-Powered CRM Dashboard")

# ===============================
# LOAD DATA DYNAMICALLY
# ===============================

conn = get_connection()
cursor = conn.cursor()

# ---- LEADS ----
cursor.execute("SELECT * FROM leads")
leads = cursor.fetchall()
lead_columns = [desc[0] for desc in cursor.description]
leads_df = pd.DataFrame(leads, columns=lead_columns)

# ---- BOOKINGS ----
cursor.execute("""
SELECT b.id, l.name, b.booking_date,
       b.booking_time, b.mode, b.status
FROM bookings b
JOIN leads l ON b.lead_id = l.id
""")

bookings = cursor.fetchall()
booking_columns = [desc[0] for desc in cursor.description]
bookings_df = pd.DataFrame(bookings, columns=booking_columns)

conn.close()

# ===============================
# METRICS
# ===============================

st.subheader("📌 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Leads", len(leads_df))
col2.metric("Total Bookings", len(bookings_df))

qualified_count = 0
if not leads_df.empty and "pipeline_stage" in leads_df.columns:
    qualified_count = len(
        leads_df[leads_df["pipeline_stage"] == "Qualified"]
    )

col3.metric("Qualified Leads", qualified_count)

hot_count = 0
if not leads_df.empty and "lead_score" in leads_df.columns:
    hot_count = len(leads_df[leads_df["lead_score"] >= 90])

col4.metric("Hot Leads", hot_count)

# ===============================
# PIPELINE BREAKDOWN
# ===============================

st.subheader("📈 Pipeline Breakdown")

if not leads_df.empty and "pipeline_stage" in leads_df.columns:
    pipeline_counts = Counter(leads_df["pipeline_stage"])
    st.bar_chart(pipeline_counts)

# ===============================
# PRIORITY SEGMENTATION
# ===============================

st.subheader("🔥 AI Lead Priority Segmentation")

if not leads_df.empty and "lead_score" in leads_df.columns:

    def categorize(score):
        if score >= 90:
            return "🔥 Hot"
        elif score >= 60:
            return "🟡 Warm"
        else:
            return "🔵 Cold"

    leads_df["Priority"] = leads_df["lead_score"].apply(categorize)

    priority_counts = Counter(leads_df["Priority"])
    st.bar_chart(priority_counts)

# ===============================
# QUALIFICATION COMPLETENESS
# ===============================

st.subheader("🧠 Qualification Completeness")

if not leads_df.empty:

    def qualification_score(row):
        fields = [
            row.get("grade"),
            row.get("interest")
        ]

        filled = sum([1 for f in fields if f not in [None, "", "null"]])
        return round((filled / len(fields)) * 100, 0)

    leads_df["Qualification %"] = leads_df.apply(
        qualification_score,
        axis=1
    )

    display_cols = [
        col for col in [
            "name",
            "pipeline_stage",
            "lead_score",
            "Qualification %",
            "Priority"
        ] if col in leads_df.columns
    ]

    st.dataframe(
        leads_df[display_cols].sort_values(
            by="lead_score",
            ascending=False
        )
    )

# ===============================
# TOP LEADS
# ===============================

st.subheader("🏆 Top 5 High-Value Leads")

if not leads_df.empty and "lead_score" in leads_df.columns:
    top_leads = leads_df.sort_values(
        by="lead_score",
        ascending=False
    ).head(5)

    st.dataframe(top_leads)

# ===============================
# FULL CRM VIEW
# ===============================

st.subheader("📋 Full CRM View")
st.dataframe(leads_df)

# ===============================
# BOOKINGS
# ===============================

st.subheader("📅 All Bookings")
st.dataframe(bookings_df)
