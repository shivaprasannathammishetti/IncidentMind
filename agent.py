import os
from dotenv import load_dotenv
from openai import OpenAI

from hindsight_memory import recall_similar_incidents, close_client

load_dotenv()

# ============================================================
# GROQ LLM CLIENT
# ============================================================

llm = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url=os.getenv("GROQ_BASE_URL")
)

MODEL = os.getenv("GROQ_MODEL")


# ============================================================
# MEMORY CONTEXT
# ============================================================

def build_memory_context(memories):
    """
    Convert Hindsight memories into a clean context
    for the LLM.
    """

    if not memories:
        return "No relevant historical incidents were found."

    context = []

    for index, memory in enumerate(memories[:5], start=1):
        context.append(
            f"PAST INCIDENT {index}:\n{memory.text}"
        )

    return "\n\n".join(context)


# ============================================================
# FILTER CURRENT INCIDENT FROM HINDSIGHT RESULTS
# ============================================================

def filter_current_incident(memories, incident):
    """
    Prevent the current/live incident from being treated
    as historical experience.

    This is important because IncidentMind must learn from
    PAST incidents, not from the incident currently being
    investigated.
    """

    current_incident_id = incident.get(
        "incident_id", ""
    ).lower()

    current_date = incident.get(
        "date", "2026-09-28"
    )

    filtered_memories = []

    for memory in memories:

        text = memory.text.lower()

        # ----------------------------------------------------
        # Rule 1: Ignore exact current incident ID
        # ----------------------------------------------------
        if current_incident_id and current_incident_id in text:
            continue

        # ----------------------------------------------------
        # Rule 2: Ignore memories containing today's incident
        # date.
        #
        # This prevents memories such as:
        # "including the 2026-09-28 incident"
        # from being used as historical evidence.
        # ----------------------------------------------------
        if current_date in text:
            continue

        filtered_memories.append(memory)

    return filtered_memories


# ============================================================
# INCIDENT ANALYSIS
# ============================================================

def analyze_incident(incident):

    # --------------------------------------------------------
    # 1. SEARCH HINDSIGHT
    # --------------------------------------------------------

    query = f"""
Service: {incident['service']}
Error: {incident['error']}
Current symptoms: {incident['symptoms']}
Environment: {incident['environment']}
"""

    memories = recall_similar_incidents(query)

    # --------------------------------------------------------
    # 2. REMOVE CURRENT INCIDENT FROM MEMORY RESULTS
    # --------------------------------------------------------

    memories = filter_current_incident(
        memories,
        incident
    )

    # --------------------------------------------------------
    # 3. BUILD MEMORY CONTEXT
    # --------------------------------------------------------

    memory_context = build_memory_context(memories)

    # --------------------------------------------------------
    # 4. BUILD REASONING PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are IncidentMind, an AI incident-response assistant
for software engineering teams.

Your job is to investigate the CURRENT INCIDENT using:

1. Current incident information
2. Historical incidents retrieved from Hindsight

IMPORTANT RULES:

- Historical incidents are evidence, not proof.
- Do NOT blindly assume an old incident is the root cause.
- Clearly distinguish hypotheses from confirmed facts.
- Never claim that a root cause is confirmed unless the
  current evidence proves it.
- Do not treat the current incident as historical experience.
- Prefer historical incidents that match the same service,
  symptoms, trigger, and error pattern.

============================================================
CURRENT INCIDENT
============================================================

Incident ID:
{incident['incident_id']}

Date:
{incident.get('date', '2026-09-28')}

Service:
{incident['service']}

Error:
{incident['error']}

Symptoms:
{incident['symptoms']}

Environment:
{incident['environment']}


============================================================
HISTORICAL EXPERIENCE FROM HINDSIGHT
============================================================

{memory_context}


============================================================
ANALYSIS REQUIREMENTS
============================================================

Provide your response using exactly these sections:

1. INCIDENT SUMMARY

Briefly summarize the current problem.


2. RELEVANT PAST EXPERIENCE

Identify the most relevant historical incident(s).

For each relevant incident explain:

- What happened previously
- What is similar to the current incident
- What is different
- Why the historical experience matters


3. LIKELY ROOT CAUSE

Give the most likely explanation based on the available
evidence.

Clearly label it as a hypothesis.

Do NOT claim it is confirmed.


4. INVESTIGATION STEPS

Give exactly 3 concrete things an SRE should check next.

Make them practical and technically useful.


5. RECOMMENDED ACTION

Give the safest immediate mitigation an SRE should consider.

The recommendation should be reversible where possible.


6. CONFIDENCE

Choose:

Low
Medium
High

Then explain why that confidence level is appropriate.
"""


    # --------------------------------------------------------
    # 5. ASK GROQ
    # --------------------------------------------------------

    response = llm.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful production incident-response "
                    "assistant. Use historical memory as evidence, "
                    "not as proof. Never claim a hypothesis is "
                    "confirmed without current evidence."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    # --------------------------------------------------------
    # 6. RETURN RESULT
    # --------------------------------------------------------

    return (
        response.choices[0].message.content,
        memories
    )


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    current_incident = {

        "incident_id": "LIVE-001",

        "date": "2026-09-28",

        "service": "Payment API",

        "error": (
            "HTTP 500 errors during payment processing"
        ),

        "symptoms": (
            "Database connections are unusually high. "
            "The incident started shortly after a traffic spike."
        ),

        "environment": "Production"
    }


    print()
    print("=" * 60)
    print("              INCIDENTMIND AI AGENT")
    print("=" * 60)
    print()

    print("🔎 Searching Hindsight for past experience...")
    print()

    answer, memories = analyze_incident(
        current_incident
    )

    print(
        f"🧠 Found {len(memories)} historical memories."
    )

    print()

    print("=" * 60)
    print("              INCIDENTMIND ANALYSIS")
    print("=" * 60)
    print()

    print(answer)

    close_client()