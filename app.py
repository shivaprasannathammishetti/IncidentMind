import os
import re
from datetime import date, datetime

import streamlit as st
from dotenv import load_dotenv
from hindsight_client import Hindsight
from openai import OpenAI


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")

HINDSIGHT_BASE_URL = os.getenv(
    "HINDSIGHT_BASE_URL",
    "https://api.hindsight.vectorize.io"
)

HINDSIGHT_BANK_ID = os.getenv(
    "HINDSIGHT_BANK_ID",
    "incidentmind"
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_BASE_URL = os.getenv(
    "GROQ_BASE_URL",
    "https://api.groq.com/openai/v1"
)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)


# ============================================================
# CHECK CONFIGURATION
# ============================================================

if not HINDSIGHT_API_KEY:
    st.error("HINDSIGHT_API_KEY is missing from .env")
    st.stop()

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing from .env")
    st.stop()


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="IncidentMind",
    page_icon="🚨",
    layout="wide"
)


# ============================================================
# CLIENTS
# ============================================================

hindsight = Hindsight(
    base_url=HINDSIGHT_BASE_URL,
    api_key=HINDSIGHT_API_KEY
)

llm = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=GROQ_BASE_URL
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def memory_text(memory):
    """
    Safely extract text from a Hindsight memory.
    """

    if hasattr(memory, "text"):
        return memory.text

    if isinstance(memory, dict):
        return memory.get("text", str(memory))

    return str(memory)


# ============================================================
# FILTER CURRENT INCIDENT FROM HINDSIGHT
# ============================================================

def is_current_incident_memory(
    memory,
    service,
    error,
    symptoms
):
    """
    Detect whether a retrieved Hindsight memory actually belongs
    to the incident currently being investigated.

    This prevents IncidentMind from showing the current incident
    as if it were historical experience.
    """

    text = memory_text(memory).lower()

    current_date = date.today().isoformat()

    service_text = service.lower()
    error_text = error.lower()
    symptoms_text = symptoms.lower()

    # --------------------------------------------------------
    # Strong indicators
    # --------------------------------------------------------

    # Current incident stored today
    if current_date in text:

        # Current service + current date
        if service_text in text:
            return True

        # Current error + current date
        error_keywords = [
            word
            for word in re.findall(r"[a-zA-Z0-9]+", error_text)
            if len(word) > 3
        ]

        matching_error_words = sum(
            1
            for word in error_keywords
            if word in text
        )

        if matching_error_words >= 2:
            return True

        # Current symptom + current date
        symptom_keywords = [
            word
            for word in re.findall(r"[a-zA-Z0-9]+", symptoms_text)
            if len(word) > 4
        ]

        matching_symptom_words = sum(
            1
            for word in symptom_keywords
            if word in text
        )

        if matching_symptom_words >= 2:
            return True

    # --------------------------------------------------------
    # Explicit live/current markers
    # --------------------------------------------------------

    current_markers = [
        "live-001",
        "current incident",
        "current production incident",
        "this incident was investigated by incidentmind"
    ]

    for marker in current_markers:
        if marker in text:
            return True

    return False


def filter_historical_memories(
    memories,
    service,
    error,
    symptoms
):
    """
    Remove memories that represent the current incident.

    We keep genuine historical incidents only.
    """

    historical = []

    for memory in memories:

        if is_current_incident_memory(
            memory,
            service,
            error,
            symptoms
        ):
            continue

        historical.append(memory)

    # --------------------------------------------------------
    # Remove duplicate memory units
    # --------------------------------------------------------
    # Hindsight can return multiple memory units for the same
    # incident. Keep one representation per incident for the UI.

    unique_memories = []
    seen_incident_ids = set()
    seen_text = set()

    for memory in historical:

        text = memory_text(memory).strip()
        lower_text = text.lower()

        ids = re.findall(
            r"\bINC-\d+\b",
            text,
            flags=re.IGNORECASE
        )

        if ids:
            incident_id = ids[0].upper()

            if incident_id in seen_incident_ids:
                continue

            seen_incident_ids.add(incident_id)
            unique_memories.append(memory)

        else:
            normalized = re.sub(r"\s+", " ", lower_text)

            if normalized in seen_text:
                continue

            seen_text.add(normalized)
            unique_memories.append(memory)

    # Maximum five UNIQUE historical memories shown to the user
    return unique_memories[:5]


# ============================================================
# HINDSIGHT RECALL
# ============================================================

def recall_incidents(
    query,
    service,
    error,
    symptoms
):
    """
    Search Hindsight and return only genuine historical incidents.

    We intentionally retrieve more than five first because some
    results may belong to the current incident and need filtering.
    """

    try:

        result = hindsight.recall(
            bank_id=HINDSIGHT_BANK_ID,
            query=query
        )

        memories = getattr(
            result,
            "results",
            []
        )

        # Get extra memories so filtering does not leave us
        # with an unnecessarily small historical set.
        memories = memories[:10]

        memories = filter_historical_memories(
            memories,
            service,
            error,
            symptoms
        )

        return memories

    except Exception as e:

        st.error(
            f"Hindsight recall failed: {e}"
        )

        return []


# ============================================================
# MEMORY SIGNAL
# ============================================================

def calculate_memory_signal(
    service,
    error,
    symptoms,
    memories
):
    """
    Transparent heuristic for the demo.

    This is NOT an ML similarity score.
    It only explains how many known incident signals
    appear in the current incident and retrieved history.
    """

    if not memories:
        return 0, "No historical pattern found"

    current_text = (
        f"{service} {error} {symptoms}"
    ).lower()

    signals = [
        "http 500",
        "database",
        "db",
        "connection",
        "pool",
        "traffic spike",
        "traffic",
        "timeout",
        "production"
    ]

    current_matches = 0

    for signal in signals:

        if signal in current_text:
            current_matches += 1

    historical_text = " ".join(
        memory_text(memory).lower()
        for memory in memories
    )

    historical_matches = 0

    for signal in signals:

        if signal in historical_text:
            historical_matches += 1

    total = (
        current_matches +
        historical_matches
    )

    if total >= 10:

        level = "Strong recurring pattern"

    elif total >= 6:

        level = "Moderate recurring pattern"

    else:

        level = "Weak recurring pattern"

    return total, level


# ============================================================
# DATE EXTRACTION
# ============================================================

def extract_dates_from_memories(memories):
    """
    Extract YYYY-MM-DD dates from Hindsight memories.
    """

    dates = []

    for memory in memories:

        text = memory_text(memory)

        matches = re.findall(
            r"\b20\d{2}-\d{2}-\d{2}\b",
            text
        )

        for value in matches:

            try:

                parsed = datetime.strptime(
                    value,
                    "%Y-%m-%d"
                ).date()

                dates.append(parsed)

            except ValueError:

                pass

    return sorted(set(dates))


# ============================================================
# PATTERN DETECTION
# ============================================================

def detect_patterns(memories):
    """
    Identify recurring patterns from historical memory.
    """

    if not memories:
        return []

    combined = " ".join(
        memory_text(memory).lower()
        for memory in memories
    )

    patterns = []

    if "http 500" in combined:
        patterns.append("HTTP 500 errors")

    if (
        "database connection" in combined
        or "db connection" in combined
    ):
        patterns.append(
            "Database connection pressure"
        )

    if "connection pool" in combined:
        patterns.append(
            "Connection-pool exhaustion"
        )

    if "traffic spike" in combined:
        patterns.append(
            "Traffic spikes"
        )

    if (
        "scaling" in combined
        or "workers" in combined
    ):
        patterns.append(
            "Worker scaling"
        )

    if "timeout" in combined:
        patterns.append(
            "Request timeouts"
        )

    return patterns[:5]


# ============================================================
# LLM ANALYSIS
# ============================================================

def analyze_with_llm(
    service,
    environment,
    error,
    symptoms,
    memories
):
    """
    Send the current incident plus historical Hindsight
    experience to Groq.
    """

    historical_context = ""

    if memories:

        for index, memory in enumerate(
            memories,
            start=1
        ):

            historical_context += (
                f"\nPAST INCIDENT {index}:\n"
                f"{memory_text(memory)}\n"
            )

    else:

        historical_context = (
            "No relevant historical incidents were found."
        )

    prompt = f"""
You are IncidentMind, an AI incident-response assistant
for software engineering and SRE teams.

Your most important capability is using historical experience
to improve the investigation of a NEW production incident.

CURRENT INCIDENT
----------------
Service: {service}
Environment: {environment}
Error: {error}
Observed symptoms: {symptoms}

HISTORICAL EXPERIENCE FROM HINDSIGHT
-------------------------------------
{historical_context}

Analyze the CURRENT incident using the historical experience.

IMPORTANT RULES:

- Historical incidents are evidence, not proof.
- Do NOT claim the root cause is confirmed unless evidence
  supports it.
- Clearly distinguish historical facts from your current
  hypothesis.
- Explain similarities and differences.
- Use previous successful resolutions as evidence.
- Recommend practical investigation steps.
- Do not automatically perform production changes.
- Keep the response useful to an SRE engineer.
- Do not pretend to have real-time production telemetry.

Return EXACTLY these six sections:

1. INCIDENT SUMMARY

Briefly summarize the current problem.

2. RELEVANT PAST EXPERIENCE

Identify the most relevant historical incidents.
Explain what is similar and why those incidents matter.

3. LIKELY ROOT CAUSE

Give the most likely explanation based on the available
evidence.

Clearly label it as a hypothesis.

4. INVESTIGATION STEPS

Give exactly 3 practical investigation steps.

5. RECOMMENDED ACTION

Give a safe immediate mitigation based on the available
evidence and previous experience.

6. CONFIDENCE

Use Low, Medium, or High and explain why.
"""

    try:

        response = llm.chat.completions.create(

            model=GROQ_MODEL,

            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a careful production "
                        "incident-response assistant. "
                        "Never claim a hypothesis is confirmed "
                        "without evidence."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.2,

            max_tokens=1800
        )

        return response.choices[0].message.content

    except Exception as e:

        return f"LLM analysis failed: {e}"


# ============================================================
# STORE INCIDENT
# ============================================================

def store_incident(
    service,
    environment,
    error,
    symptoms,
    analysis
):
    """
    Store the reviewed incident in Hindsight so future
    incidents can learn from it.
    """

    incident_date = date.today()

    content = f"""
IncidentMind historical incident record

Incident date: {incident_date}
Service: {service}
Environment: {environment}
Error: {error}
Observed symptoms: {symptoms}

AI investigation:
{analysis}

This incident was investigated and reviewed by IncidentMind.
It is now stored as historical team experience for future
incident-response learning.
"""

    try:

        hindsight.retain(
            bank_id=HINDSIGHT_BANK_ID,
            content=content
        )

        return True, None

    except Exception as e:

        return False, str(e)


# ============================================================
# SESSION STATE
# ============================================================

if "analysis" not in st.session_state:

    st.session_state.analysis = None


if "memories" not in st.session_state:

    st.session_state.memories = []


if "incident_data" not in st.session_state:

    st.session_state.incident_data = None


if "stored" not in st.session_state:

    st.session_state.stored = False


# ============================================================
# HEADER
# ============================================================

st.title("🚨 IncidentMind")

st.subheader(
    "AI Incident Response That Learns From Past Experience"
)

st.write(
    "IncidentMind helps software teams investigate production "
    "incidents by combining **current incident signals** with "
    "**historical team experience stored in Hindsight**."
)

st.divider()


# ============================================================
# CURRENT INCIDENT
# ============================================================

st.header("🚨 Current Incident")

col1, col2 = st.columns(2)

with col1:

    service = st.selectbox(
        "Service",
        [
            "Payment API",
            "Order Service",
            "Authentication API",
            "Notification Service",
            "User Profile API",
            "Inventory Service",
            "Search API"
        ]
    )


with col2:

    environment = st.selectbox(
        "Environment",
        [
            "Production",
            "Staging",
            "Development"
        ]
    )


col1, col2 = st.columns(2)

with col1:

    error = st.text_input(
        "Error",
        value="HTTP 500 errors during payment processing"
    )


with col2:

    symptoms = st.text_area(
        "Observed Symptoms",
        value=(
            "Database connections are unusually high. "
            "The issue started shortly after a traffic spike."
        ),
        height=100
    )


# ============================================================
# INVESTIGATE BUTTON
# ============================================================

if st.button(
    "🔍 Investigate Incident",
    type="primary",
    use_container_width=True
):

    st.session_state.stored = False

    query = f"""
Current production incident:

Service: {service}
Error: {error}
Symptoms: {symptoms}

Find PREVIOUS and HISTORICAL incidents involving similar:

- service
- error
- symptoms
- root causes
- triggers
- resolutions

IMPORTANT:
Do not return the current incident as historical experience.
"""

    with st.spinner(
        "🧠 Searching Hindsight for past experience..."
    ):

        memories = recall_incidents(
            query,
            service,
            error,
            symptoms
        )

    st.session_state.memories = memories

    with st.spinner(
        "🤖 Reasoning over current and historical incidents..."
    ):

        analysis = analyze_with_llm(
            service,
            environment,
            error,
            symptoms,
            memories
        )

    st.session_state.analysis = analysis

    st.session_state.incident_data = {

        "service": service,

        "environment": environment,

        "error": error,

        "symptoms": symptoms
    }


# ============================================================
# SHOW RESULTS
# ============================================================

if st.session_state.analysis:

    st.divider()

    st.header("🧠 IncidentMind Analysis")

    memories = st.session_state.memories


    # ========================================================
    # MEMORY INSIGHT
    # ========================================================

    st.subheader(
        "🧠 What IncidentMind Remembered"
    )

    if memories:

        signal_score, signal_level = (
            calculate_memory_signal(
                service,
                error,
                symptoms,
                memories
            )
        )

        patterns = detect_patterns(memories)

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Hindsight Memories",
                len(memories)
            )

        with col2:

            st.metric(
                "Memory Signal",
                signal_level
            )

        with col3:

            st.metric(
                "Recurring Signals",
                len(patterns)
            )

        st.success(
            "🔗 IncidentMind connected this incident "
            "to previous team experience stored in Hindsight."
        )

        if patterns:

            st.markdown(
                "**Recurring patterns detected:**"
            )

            for pattern in patterns:

                st.markdown(
                    f"- 🔄 {pattern}"
                )

        st.info(
            "**Why this matters:** "
            "The agent is not reasoning only from the current "
            "incident. It is using previous incidents as evidence "
            "to guide the investigation."
        )

    else:

        st.warning(
            "No historical memory was retrieved for this incident."
        )


    # ========================================================
    # MEMORY TIMELINE
    # ========================================================

    if memories:

        st.subheader(
            "🕐 Incident Memory Timeline"
        )

        dates = extract_dates_from_memories(
            memories
        )

        if dates:

            timeline_columns = st.columns(
                min(len(dates), 4)
            )

            for index, incident_date in enumerate(
                dates[-4:]
            ):

                with timeline_columns[
                    index % len(timeline_columns)
                ]:

                    st.markdown(
                        f"**📅 {incident_date}**"
                    )

                    st.caption(
                        "Historical experience recalled"
                    )

        st.caption(
            "These dates come from historical incidents "
            "retrieved from the Hindsight memory bank."
        )


    # ========================================================
    # PAST EXPERIENCE
    # ========================================================

    st.subheader(
        "🧠 Relevant Past Experience"
    )

    st.info(
        f"IncidentMind found **{len(memories)} "
        f"historical memory units in Hindsight.**"
    )

    if memories:

        for index, memory in enumerate(
            memories,
            start=1
        ):

            with st.expander(
                f"Past Experience #{index}",
                expanded=(index <= 3)
            ):

                st.write(
                    memory_text(memory)
                )

    else:

        st.warning(
            "No relevant historical experience was found."
        )


    # ========================================================
    # AI ANALYSIS
    # ========================================================

    st.subheader(
        "🎯 AI Investigation"
    )

    st.markdown(
        st.session_state.analysis
    )


    # ========================================================
    # TEACH INCIDENTMIND
    # ========================================================

    st.divider()

    st.subheader(
        "🧠 Teach IncidentMind"
    )

    st.write(
        "Once this incident has been reviewed and resolved, "
        "store it in Hindsight so a future incident can learn "
        "from this experience."
    )

    if not st.session_state.stored:

        if st.button(
            "💾 Store This Incident in Hindsight",
            use_container_width=True
        ):

            data = st.session_state.incident_data

            with st.spinner(
                "🧠 Storing new incident experience..."
            ):

                success, error_message = store_incident(
                    data["service"],
                    data["environment"],
                    data["error"],
                    data["symptoms"],
                    st.session_state.analysis
                )

            if success:

                st.session_state.stored = True

                st.success(
                    "✅ Incident stored successfully in Hindsight!"
                )

                st.info(
                    "🧠 IncidentMind has learned from this "
                    "incident. Future incidents can retrieve "
                    "this experience."
                )

            else:

                st.error(
                    f"Failed to store incident: "
                    f"{error_message}"
                )

    else:

        st.success(
            "🧠 This incident has already been stored "
            "in Hindsight for future learning."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "IncidentMind • Powered by Hindsight memory + Groq reasoning"
)