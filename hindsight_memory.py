import os
import json
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

# Connect to Hindsight Cloud
client = Hindsight(
    base_url=os.getenv("HINDSIGHT_BASE_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY")
)

BANK_ID = os.getenv("HINDSIGHT_BANK_ID")


def format_incident(incident):
    """Convert an incident dictionary into useful memory text."""

    return f"""
Production Incident:

Incident ID: {incident['incident_id']}
Service: {incident['service']}
Error: {incident['error']}
Root Cause: {incident['root_cause']}
Resolution: {incident['resolution']}
Environment: {incident['environment']}
Date: {incident['date']}
Impact: {incident['impact']}
"""


def store_incident(incident):
    """Store one incident in Hindsight."""

    memory_text = format_incident(incident)

    return client.retain(
        bank_id=BANK_ID,
        content=memory_text
    )


def load_incidents():
    """Load historical incidents from JSON."""

    with open("data/incidents.json", "r", encoding="utf-8") as file:
        return json.load(file)


def load_all_incidents():
    """Store all historical incidents in Hindsight."""

    incidents = load_incidents()

    print(f"Found {len(incidents)} historical incidents.")

    for incident in incidents:
        print(
            f"Storing {incident['incident_id']} - "
            f"{incident['service']}..."
        )

        store_incident(incident)

    print("\n✅ All historical incidents stored successfully!")


def recall_similar_incidents(query):
    """Find relevant historical incidents."""

    result = client.recall(
        bank_id=BANK_ID,
        query=query
    )

    return result.results
def close_client():
    """Close the Hindsight connection."""
    client.close()

if __name__ == "__main__":

    print("====================================")
    print("      INCIDENTMIND MEMORY LOADER")
    print("====================================\n")

    load_all_incidents()

    print("\nTesting memory recall...\n")

    query = """
    Payment API is returning HTTP 500 errors.
    Database connections are unusually high after a traffic spike.
    """

    memories = recall_similar_incidents(query)

    print("===== RELEVANT PAST INCIDENTS =====")

    for memory in memories[:5]:
        print("\n" + memory.text)

    client.close()