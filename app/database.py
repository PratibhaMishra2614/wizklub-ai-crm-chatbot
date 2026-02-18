import sqlite3
from datetime import datetime
from datetime import datetime
import os

# Force DB to root directory explicitly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "wizklub.db")

print("Database path:", DB_PATH)



# ===============================
# CONNECTION
# ===============================

def get_connection():
    return sqlite3.connect(DB_PATH)


# ===============================
# INITIALIZE DATABASE
# ===============================

def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Leads Table (Upgraded Schema)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        phone TEXT,
        user_type TEXT,
        grade TEXT,
        interest TEXT,
        urgency TEXT,
        program_interest TEXT,
        budget_signal TEXT,
        extracted_intent TEXT,
        lead_score INTEGER DEFAULT 0,
        pipeline_stage TEXT DEFAULT 'New',
        created_at TEXT
    )
    """)

    # Bookings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER,
        booking_date TEXT,
        booking_time TEXT,
        mode TEXT,
        status TEXT DEFAULT 'Scheduled',
        created_at TEXT,
        FOREIGN KEY (lead_id) REFERENCES leads(id)
    )
    """)

    conn.commit()
    conn.close()


# ===============================
# LEAD OPERATIONS
# ===============================

def save_lead(name, email, phone, user_type,
              grade=None,
              interest=None,
              urgency=None,
              program_interest=None,
              budget_signal=None,
              extracted_intent=None,
              lead_score=0):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO leads (
            name, email, phone, user_type,
            grade, interest,
            urgency, program_interest,
            budget_signal, extracted_intent,
            lead_score, pipeline_stage, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            email,
            phone,
            user_type,
            grade,
            interest,
            urgency,
            program_interest,
            budget_signal,
            extracted_intent,
            lead_score,
            "New",
            datetime.now()
        ))

        conn.commit()

    except sqlite3.IntegrityError:
        # Email already exists
        pass

    conn.close()


def get_lead_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM leads WHERE email = ?", (email,))
    lead = cursor.fetchone()

    conn.close()
    return lead


def update_pipeline_stage(lead_id, stage):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE leads SET pipeline_stage = ?
    WHERE id = ?
    """, (stage, lead_id))

    conn.commit()
    conn.close()


def increase_lead_score(lead_id, increment):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE leads
    SET lead_score = lead_score + ?
    WHERE id = ?
    """, (increment, lead_id))

    conn.commit()
    conn.close()


# ===============================
# NEW: UPDATE QUALIFICATION SIGNALS
# ===============================

def update_lead_signals(lead_id, signals):
    """
    Updates structured AI extracted signals.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE leads
    SET grade = COALESCE(?, grade),
        program_interest = COALESCE(?, program_interest),
        urgency = COALESCE(?, urgency),
        budget_signal = COALESCE(?, budget_signal),
        extracted_intent = COALESCE(?, extracted_intent)
    WHERE id = ?
    """, (
        signals.get("grade"),
        signals.get("program_interest"),
        signals.get("urgency"),
        signals.get("budget_signal"),
        signals.get("intent"),
        lead_id
    ))

    conn.commit()
    conn.close()


# ===============================
# BOOKING OPERATIONS
# ===============================

def is_slot_available(booking_date, booking_time):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*) FROM bookings
    WHERE booking_date = ? AND booking_time = ?
    """, (booking_date, booking_time))

    count = cursor.fetchone()[0]
    conn.close()

    return count == 0


def save_booking(lead_id, booking_date, booking_time, mode):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO bookings (
        lead_id,
        booking_date,
        booking_time,
        mode,
        status,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        lead_id,
        booking_date,
        booking_time,
        mode,
        "Scheduled",
        datetime.now()
    ))

    conn.commit()
    conn.close()


def get_bookings_by_lead(lead_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT booking_date, booking_time, mode, status
    FROM bookings
    WHERE lead_id = ?
    """, (lead_id,))

    results = cursor.fetchall()
    conn.close()
    return results


# ===============================
# ADMIN QUERIES
# ===============================

def get_all_leads():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM leads")
    leads = cursor.fetchall()

    conn.close()
    return leads


def get_all_bookings():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT b.id, l.name, b.booking_date,
           b.booking_time, b.mode, b.status
    FROM bookings b
    JOIN leads l ON b.lead_id = l.id
    """)

    bookings = cursor.fetchall()
    conn.close()
    return bookings
