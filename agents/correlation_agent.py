"""
ChestGuard NeuralScan — Correlation Agent
Agent 2: Cross-references AI findings with patient symptoms.
"""
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS


def get_llm():
    return ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS
    )


CORRELATION_PROMPT = ChatPromptTemplate.from_template("""
You are Agent 2 (Symptom Correlation Specialist) in the ChestGuard NeuralScan multi-agent pipeline.
You receive the Screening Agent's report and cross-reference with patient-reported symptoms.

SCREENING AGENT REPORT:
{screening_report}

PATIENT INFORMATION:
- Age: {age}
- Gender: {gender}
- Reported Symptoms: {symptoms}
- Smoking History: {smoking}
- Pre-existing Conditions: {conditions}

YOUR TASK — Provide correlation analysis:

1. **SYMPTOM-FINDING CORRELATION**:
   - Which symptoms MATCH the imaging findings? (High correlation)
   - Which symptoms are UNEXPLAINED by imaging? (Needs further investigation)
   - Which findings have NO reported symptoms? (Silent/subclinical)

2. **RISK FACTOR ANALYSIS**:
   - How do the patient's risk factors (age, smoking, comorbidities) relate to findings?
   - Are findings expected given the patient profile?

3. **CLINICAL SIGNIFICANCE**:
   - Rate the overall correlation: STRONG / MODERATE / WEAK
   - Highlight any DISCREPANCIES that warrant attention

Be precise and clinical. Use bullet points. This report feeds into the Risk Agent.
""")


def run(screening_report, patient_info):
    """
    Run the Correlation Agent.

    Args:
        screening_report: output from Agent 1
        patient_info: dict with patient data

    Returns:
        dict with agent output
    """
    llm = get_llm()
    chain = CORRELATION_PROMPT | llm

    response = chain.invoke({
        "screening_report": screening_report,
        "age": patient_info.get("age", "Not provided"),
        "gender": patient_info.get("gender", "Not provided"),
        "symptoms": patient_info.get("symptoms", "None reported"),
        "smoking": patient_info.get("smoking", "Not provided"),
        "conditions": patient_info.get("conditions", "None reported")
    })

    return {
        "agent": "Correlation Specialist",
        "icon": "🔗",
        "output": response.content,
        "status": "complete"
    }
