"""
ChestGuard NeuralScan — Recommendation Agent
Agent 4: Synthesizes all findings into actionable recommendations.
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


RECOMMENDATION_PROMPT = ChatPromptTemplate.from_template("""
You are Agent 4 (Clinical Recommendation Specialist) in the ChestGuard NeuralScan multi-agent pipeline.
You are the FINAL agent. Synthesize ALL previous findings into clear, actionable recommendations.

COMPLETE ANALYSIS CHAIN:
1. Screening Report: {screening_report}
2. Correlation Report: {correlation_report}
3. Risk Assessment: {risk_report}

PATIENT PROFILE:
- Age: {age}, Gender: {gender}
- NeuralScore™: {neural_score}/100 (Risk: {risk_tier})

YOUR TASK — Provide final recommendations:

1. **📋 EXECUTIVE SUMMARY** (2-3 sentences):
   - Overall assessment in plain language
   - Urgency level: ROUTINE / PRIORITY / URGENT / EMERGENCY

2. **🏥 SPECIALIST REFERRALS**:
   - Which specialists to consult (pulmonologist, cardiologist, etc.)
   - Priority order and expected timeline

3. **🔬 RECOMMENDED TESTS**:
   - Additional imaging (CT scan, MRI, etc.)
   - Laboratory tests (blood work, cultures, etc.)
   - Functional tests (spirometry, ECG, etc.)

4. **💊 IMMEDIATE ACTIONS**:
   - What to do right now
   - Precautions to take
   - Symptoms to watch for

5. **🌿 LIFESTYLE RECOMMENDATIONS**:
   - Diet and exercise guidance
   - Environmental precautions
   - Smoking cessation resources (if applicable)
   - Mental health support

6. **📅 FOLLOW-UP PLAN**:
   - Suggested follow-up imaging timeline
   - Monitoring milestones
   - When to return for re-assessment

⚠️ ALWAYS END WITH: "This is an AI-assisted screening, not a medical diagnosis. 
Please consult a qualified healthcare professional for definitive evaluation and treatment."

Be practical, specific, and empathetic. Prioritize actionability.
""")


def run(screening_report, correlation_report, risk_report, patient_info, neural_score_data):
    """
    Run the Recommendation Agent (final agent).

    Args:
        screening_report: output from Agent 1
        correlation_report: output from Agent 2
        risk_report: output from Agent 3
        patient_info: patient data dict
        neural_score_data: NeuralScore result dict

    Returns:
        dict with agent output
    """
    llm = get_llm()
    chain = RECOMMENDATION_PROMPT | llm

    response = chain.invoke({
        "screening_report": screening_report,
        "correlation_report": correlation_report,
        "risk_report": risk_report,
        "age": patient_info.get("age", "Not provided"),
        "gender": patient_info.get("gender", "Not provided"),
        "neural_score": neural_score_data["score"],
        "risk_tier": neural_score_data["tier"]["level"]
    })

    return {
        "agent": "Clinical Recommendations",
        "icon": "💡",
        "output": response.content,
        "status": "complete"
    }
