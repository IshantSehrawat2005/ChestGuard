"""
ChestGuard NeuralScan — Screening Agent
Agent 1: Analyzes raw DenseNet predictions + GradCAM focus areas.
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


SCREENING_PROMPT = ChatPromptTemplate.from_template("""
You are Agent 1 (Screening Specialist) in the ChestGuard NeuralScan multi-agent diagnostic pipeline.
Your role: Analyze raw deep learning predictions and identify clinically significant findings.

X-RAY MODEL PREDICTIONS (DenseNet-121, all 18 pathologies):
{results}

TOP 5 CONDITIONS WITH HIGHEST PROBABILITY:
{top_findings}

GradCAM FOCUS AREAS:
The AI model focused most strongly on the following conditions (heatmap analysis available):
{heatmap_conditions}

YOUR TASK — Provide a structured screening report:

1. **PRIMARY FINDINGS** (2-3 most clinically significant conditions detected):
   - What each condition means in simple terms
   - Confidence level assessment (is the probability meaningful?)
   - What the GradCAM heatmap focus suggests

2. **NOTABLE SECONDARY FINDINGS**:
   - Any other conditions worth mentioning
   - False positive assessment (conditions that might be noise)

3. **IMAGING QUALITY ASSESSMENT**:
   - Based on prediction distribution, comment on image quality
   - Any concerns about reliability

Be concise, clinical, and structured. Use bullet points. Do NOT make a diagnosis.
This is a screening report that will be passed to the next specialist agent.
""")


def run(results, top_findings, heatmap_conditions):
    """
    Run the Screening Agent.

    Args:
        results: full prediction results dict
        top_findings: top 5 findings dict
        heatmap_conditions: list of conditions with GradCAM heatmaps

    Returns:
        dict with agent output
    """
    llm = get_llm()
    chain = SCREENING_PROMPT | llm

    response = chain.invoke({
        "results": str(results),
        "top_findings": str(top_findings),
        "heatmap_conditions": ", ".join(heatmap_conditions) if heatmap_conditions else "Not available"
    })

    return {
        "agent": "Screening Specialist",
        "icon": "🔬",
        "output": response.content,
        "status": "complete"
    }
