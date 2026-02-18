import streamlit as st
from database import (
    initialize_db,
    get_lead_by_email,
    save_booking,
    is_slot_available,
    update_pipeline_stage,
    increase_lead_score
)
from lead_manager import save_lead
from chat_engine import (
    load_vector_store,
    retrieve_chunks,
    generate_response,
    classify_user_type
)

# ===============================
# INITIALIZE DATABASE
# ===============================

initialize_db()

# ===============================
# PAGE CONFIG
# ===============================

st.set_page_config(page_title="WizKlub AI Assistant", page_icon="🎓")

st.title("🎓 WizKlub AI Assistant")
st.caption("STEM Programs | School Partnerships | Demo Booking")

# ===============================
# LOAD VECTOR STORE
# ===============================

index, chunks = load_vector_store()

# ===============================
# SESSION STATE INIT
# ===============================

defaults = {
    "chat_history": [],
    "user_type": None,
    "lead_captured": False,
    "last_user_input": "",
    "user_email": None,
    "crm_data": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ===============================
# CHAT INPUT
# ===============================

user_input = st.chat_input("Ask about WizKlub programs...")

if user_input:

    st.session_state.last_user_input = user_input

    detected_type = classify_user_type(user_input)
    if detected_type:
        st.session_state.user_type = detected_type

    # Refresh CRM data
    if st.session_state.user_email:
        st.session_state.crm_data = get_lead_by_email(
            st.session_state.user_email
        )

    context_chunks = retrieve_chunks(user_input, index, chunks)

    response = generate_response(
        query=user_input,
        context_chunks=context_chunks,
        chat_history=st.session_state.chat_history,
        user_type=st.session_state.user_type,
        crm_data=st.session_state.crm_data
    )

    st.session_state.chat_history.append(("user", user_input))
    st.session_state.chat_history.append(("assistant", response))

# ===============================
# DISPLAY CHAT HISTORY
# ===============================

for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.write(message)

# ===============================
# LEAD CAPTURE
# ===============================

st.divider()
st.subheader("📋 Book a Free Demo / Consultation")

if not st.session_state.lead_captured:

    with st.form("lead_form", clear_on_submit=False):

        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone Number")

        submit = st.form_submit_button("Submit Details")

        if submit:
            if name.strip() and email.strip() and phone.strip():

                save_lead(
                    name=name,
                    email=email,
                    phone=phone,
                    user_type=st.session_state.user_type or "Unknown",
                    intent=st.session_state.last_user_input
                )

                st.session_state.user_email = email
                st.session_state.lead_captured = True
                st.session_state.crm_data = get_lead_by_email(email)

                st.success("✅ Lead saved successfully!")

            else:
                st.warning("Please fill all fields before submitting.")

else:
    st.success("🎉 Your details are saved in our CRM.")

# ===============================
# DEMO BOOKING
# ===============================

if st.session_state.user_email:

    st.divider()
    st.subheader("📅 Schedule Demo Session")

    with st.form("booking_form"):

        booking_date = st.date_input("Select Date")
        booking_time = st.selectbox(
            "Select Time Slot",
            ["10:00 AM", "2:00 PM", "4:00 PM"]
        )
        mode = st.selectbox(
            "Mode",
            ["Online", "Offline"]
        )

        book_submit = st.form_submit_button("Confirm Booking")

        if book_submit:

            lead = get_lead_by_email(st.session_state.user_email)

            if lead:

                if is_slot_available(str(booking_date), booking_time):

                    save_booking(
                        lead_id=lead[0],
                        booking_date=str(booking_date),
                        booking_time=booking_time,
                        mode=mode
                    )

                    update_pipeline_stage(lead[0], "Booked")
                    increase_lead_score(lead[0], 30)

                    st.session_state.crm_data = get_lead_by_email(
                        st.session_state.user_email
                    )

                    st.success(
                        f"✅ Demo booked for {booking_date} at {booking_time}."
                    )

                else:
                    st.error("⚠ This slot is already booked.")

            else:
                st.warning("Lead not found.")
