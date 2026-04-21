"""
ChestGuard NeuralScan — Risk Stratification Agent
Agent 3: Interprets NeuralScore and generates risk narrative.
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


RISK_PROMPT = ChatPromptTemplate.from_template("""
You are Agent 3 (Risk Stratification Specialist) in the ChestGuard NeuralScan multi-agent pipeline.
You interpret the composite NeuralScore™ and generate a personalized risk narrative.

PREVIOUS AGENT REPORTS:
Screening: {screening_report}
Correlation: {correlation_report}

NEURALSCORE™ DATA:
- Composite Score: {neural_score}/100
- Risk Tier: {risk_tier}
- Score Breakdown:
  {score_breakdown}

REGIONAL ANALYSIS:
{region_summary}

YOUR TASK — Provide risk stratification narrative:

1. **RISK INTERPRETATION**:
   - What does the NeuralScore of {neural_score} mean for this patient?
   - Explain the risk tier ({risk_tier}) in patient-friendly terms
   - Which risk factors are contributing most?

2. **FACTOR-BY-FACTOR ANALYSIS**:
   - Imaging contribution explanation
   - Age-related risk context
   - Smoking impact assessment
   - Symptom correlation significance
   - Comorbidity influence

3. **REGIONAL RISK MAP**:
   - Which anatomical regions show the highest concern?
   - Any region-specific risks to monitor?

4. **COMPARATIVE CONTEXT**:
   - How does this risk level compare to general population norms?
   - What does this mean for the patient's prognosis?

Be empathetic but honest. Use accessible language. Avoid being alarmist but don't downplay real risks.
""")


def run(screening_report, correlation_report, neural_score_data, region_data):
    """
    Run the Risk Stratification Agent.

    Args:
        screening_report: output from Agent 1
        correlation_report: output from Agent 2
        neural_score_data: NeuralScore result dict
        region_data: regional analysis results

    Returns:
        dict with agent output
    """
    llm = get_llm()
    chain = RISK_PROMPT | llm

    # Format score breakdown
    breakdown_str = ""
    for key, data in neural_score_data.get("breakdown", {}).items():
        breakdown_str += f"  - {data['label']}: {data['score']}/100 (contributes {data['contribution']} points)\n"

    # Format region summary
    region_summary = ""
    for region_name, region_info in region_data.items():
        region_summary += f"  - {region_name}: Health={region_info['health_score']}%, Status={region_info['status']}\n"

    response = chain.invoke({
        "screening_report": screening_report,
        "correlation_report": correlation_report,
        "neural_score": neural_score_data["score"],
        "risk_tier": neural_score_data["tier"]["level"],
        "score_breakdown": breakdown_str,
        "region_summary": region_summary
    })

    return {
        "agent": "Risk Stratification",
        "icon": "📊",
        "output": response.content,
        "status": "complete"
    }
