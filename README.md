


IncidentMind 🚨🧠
AI Incident Response Agent That Learns From Past Production Incidents
IncidentMind is an AI-powered incident investigation assistant for software teams.

It uses Hindsight memory to remember previous production incidents, including symptoms, root-cause hypotheses, investigation steps, and resolutions. When a new incident occurs, IncidentMind retrieves relevant past experiences and uses them as context for an AI-assisted investigation.

The goal is simple:

Don't investigate every incident from scratch. Learn from what happened before.

🎯 Problem
Software teams frequently investigate production incidents under time pressure.

A new incident may look different on the surface, but important patterns can repeat:

Traffic spikes

Database connection pressure

Connection-pool exhaustion

Increased request latency

Downstream service failures

Repeated HTTP errors

Incident knowledge is often scattered across tickets, logs, documentation, and engineers' previous experiences.

IncidentMind turns previous incident experience into reusable memory.

💡 Solution
IncidentMind combines:

Current Incident + Hindsight Memory + LLM Reasoning

When an incident is investigated, IncidentMind:

Captures the current incident details.

Retrieves relevant historical experiences from Hindsight.

Identifies recurring signals and similar incidents.

Provides the historical context to the LLM.

Generates an investigation based on both current symptoms and past experience.

Suggests practical investigation steps and mitigation actions.

Allows the reviewed incident to be stored back into Hindsight.

Makes that experience available to future investigations.

🧠 Why Memory Matters
Memory is the central part of IncidentMind.

Without memory:

New Incident
     ↓
LLM
     ↓
Generic Investigation
With Hindsight memory:

                    ┌──────────────────────┐
                    │   Previous Incidents │
                    └──────────┬───────────┘
                               ↓
New Incident → Hindsight Recall → Relevant Experience
                               ↓
                         LLM Reasoning
                               ↓
                  Investigation + Actions
                               ↓
                     Reviewed Resolution
                               ↓
                       Hindsight Retain
                               ↓
                    Future Incident Memory
This creates a learning loop where reviewed incidents can become useful experience for future investigations.

🏗️ Architecture
┌───────────────────────┐
│     SRE / Engineer    │
└───────────┬───────────┘
            │
            │ Current Incident
            ↓
┌───────────────────────┐
│    IncidentMind UI    │
│       Streamlit       │
└───────────┬───────────┘
            │
            ↓
┌───────────────────────┐
│   Incident Agent      │
│   Python Application  │
└───────────┬───────────┘
            │
      ┌─────┴─────┐
      ↓           ↓
┌───────────┐  ┌───────────────┐
│ Hindsight │  │ LLM Reasoning │
│  Memory   │  │     Groq      │
└─────┬─────┘  └───────┬───────┘
      │                │
      └───────┬────────┘
              ↓
┌────────────────────────────┐
│ AI Investigation           │
│ • Incident Summary         │
│ • Relevant Past Experience │
│ • Root Cause Hypothesis    │
│ • Investigation Steps      │
│ • Recommended Action       │
│ • Confidence               │
└─────────────┬──────────────┘
              │
              ↓
      Store Reviewed Incident
              │
              ↓
        Hindsight Memory
🔄 Example Incident
Consider a Payment API incident:

Service:
Payment API

Environment:
Production

Error:
HTTP 504 Gateway Timeout during checkout

Symptoms:
Database connection utilization is at 92%.
Request latency has increased sharply after a traffic spike.
Several checkout requests are timing out.
IncidentMind recalls a previous incident where:

Payment API
Traffic spike
Database connection-pool exhaustion
18% payment failure rate

Resolution:
Increased connection-pool capacity
+
Scaled application workers
Instead of treating the historical incident as proof of the current root cause, IncidentMind uses it as evidence for investigation.

The resulting analysis can recommend checking:

Database connection-pool utilization

Connection wait queues

Request latency versus database wait time

Application worker capacity

Downstream payment-gateway latency

This helps engineers investigate the current incident using relevant historical experience.

🧠 Hindsight Memory
IncidentMind uses Hindsight as its memory layer.

Hindsight enables the application to:

Retain
Store reviewed incident experiences for future use.

Incident
   ↓
Analysis
   ↓
Resolution / Learning
   ↓
Hindsight Memory
Recall
Retrieve relevant experiences when a new incident occurs.

New Incident
   ↓
Hindsight Recall
   ↓
Relevant Historical Incidents
The recalled experiences are then provided to the reasoning model as contextual evidence.

🤖 AI Investigation
The AI investigation is structured into six sections:

1. Incident Summary
A concise description of the current incident.

2. Relevant Past Experience
Historical incidents that match the current symptoms.

3. Likely Root Cause
A hypothesis based on the current evidence and historical patterns.

4. Investigation Steps
Concrete checks that an engineer can perform.

5. Recommended Action
Potential immediate mitigation steps.

6. Confidence
A confidence level that reflects the available evidence and remaining uncertainty.

IncidentMind does not treat historical memory as guaranteed proof of the current root cause.

🛠️ Technology Stack
Technology	Purpose
Python	Application and agent logic
Streamlit	Interactive web interface
Hindsight	Long-term incident memory
Groq	LLM reasoning
OpenAI-compatible API	LLM integration
JSON	Sample incident data
python-dotenv	Environment configuration
📁 Project Structure
IncidentMind/
│
├── app.py
│   └── Streamlit application and UI
│
├── agent.py
│   └── Incident investigation and reasoning logic
│
├── hindsight_memory.py
│   └── Hindsight memory operations
│
├── clear_memory.py
│   └── Utility for clearing memory during development
│
├── data/
│   └── incidents.json
│       └── Sample incident data
│
├── requirements.txt
│   └── Python dependencies
│
├── .gitignore
│   └── Prevents secrets and virtual environments from being committed
│
└── README.md
⚙️ Setup
1. Clone the repository
git clone https://github.com/shivaprasannathammishetti/IncidentMind.git
cd IncidentMind
2. Create a virtual environment
python -m venv venv
Activate it on Windows:

venv\Scripts\activate
3. Install dependencies
pip install -r requirements.txt
4. Configure environment variables
Create a .env file in the project root:

HINDSIGHT_API_KEY=your_hindsight_api_key
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
HINDSIGHT_BANK_ID=incidentmind

GROQ_API_KEY=your_groq_api_key
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=openai/gpt-oss-120b
Never commit .env or API keys to GitHub.

5. Run IncidentMind
streamlit run app.py
The application will open in your browser.

🔐 Security
API credentials are loaded through environment variables.

The repository intentionally excludes:

.env
venv/
__pycache__/
*.pyc
Never hard-code API keys directly into the source code.

🚀 Demo Workflow
The application can be demonstrated using the following workflow:

1. Enter a new production incident
             ↓
2. Click "Investigate"
             ↓
3. IncidentMind recalls historical experiences
             ↓
4. Recurring patterns are identified
             ↓
5. LLM analyzes current + historical context
             ↓
6. Investigation and mitigation are generated
             ↓
7. Review the incident
             ↓
8. Store the incident in Hindsight
             ↓
9. Future incidents can retrieve this experience
📈 Example Learning Loop
First incident
IncidentMind investigates a Payment API problem and learns:

Traffic spike
        ↓
Database connection pressure
        ↓
Connection-pool exhaustion
        ↓
Payment failures
        ↓
Increase pool capacity + scale workers
Future incident
A later incident shows:

Traffic spike
+
High database connection utilization
+
Request timeouts
IncidentMind can retrieve the previous experience and use it to guide the investigation.

The previous incident does not automatically determine the new root cause; it provides relevant context for the engineer and reasoning model.

🎯 Design Principles
Memory First
Memory is not just an additional feature. Historical experience is part of the investigation workflow.

Evidence Over Assumptions
Past incidents provide evidence, not proof.

Human-in-the-Loop
IncidentMind assists engineers with investigation and recommendations. It does not autonomously modify production systems.

Learn From Experience
Reviewed incidents can become reusable knowledge for future investigations.

Explainable Investigation
The system exposes the historical incidents and reasoning context used to generate recommendations.

⚠️ Current Limitations
IncidentMind is an investigation assistant and does not directly access a company's live production infrastructure.

It does not currently:

Automatically modify production systems

Execute remediation commands

Directly access live Prometheus/Grafana telemetry

Guarantee the predicted root cause

Replace human incident-response decisions

Historical incidents are treated as contextual evidence and should be validated against current production telemetry.

🔮 Future Improvements
Possible future improvements include:

Integration with Prometheus and Grafana

Integration with OpenTelemetry traces

Slack incident-channel integration

Automatic incident timeline generation

Service dependency graphs

More advanced incident clustering

Incident severity prediction

Post-incident report generation

Team-specific operational memory

Automated learning from resolved incident tickets

📌 Project Status
IncidentMind currently provides:

✅ Historical incident memory

✅ Hindsight recall

✅ Incident pattern detection

✅ AI-assisted investigation

✅ Root-cause hypothesis generation

✅ Investigation recommendations

✅ Mitigation suggestions

✅ Incident learning through Hindsight retention

✅ Interactive Streamlit interface

✅ Human-in-the-loop workflow

🧠 Core Idea
Every incident should make the next investigation smarter.

IncidentMind turns previous incident experience into reusable memory so engineers can investigate recurring production problems with more context and less repetition.