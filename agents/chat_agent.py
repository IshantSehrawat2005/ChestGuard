"""
ChestGuard NeuralScan — Chat Agent
Conversational follow-up agent with full analysis context.
"""
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS


def get_llm():
    return ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name=LLM_MODEL,
        temperature=0.4,
        max_tokens=1024
    )


CHAT_PROMPT = ChatPromptTemplate.from_template("""
You are ChestGuard NeuralScan AI Assistant — a medical screening chatbot.
You have complete context from a patient's chest X-ray analysis.

ANALYSIS CONTEXT:
- Top Findings: {top_findings}
- NeuralScore™: {neural_score}/100 (Risk: {risk_tier})
- Regional Analysis: {region_summary}

MULTI-AGENT ANALYSIS SUMMARY:
{analysis_summary}

PATIENT INFO:
Age: {age}, Gender: {gender}, Symptoms: {symptoms}

CONVERSATION HISTORY:
{chat_history}

PATIENT'S QUESTION: {question}

RULES:
1. Answer based on the X-ray analysis context above
2. Be helpful, empathetic, and use simple language
3. Reference specific findings when relevant
4. Always remind them this is AI-assisted screening, not diagnosis
5. If asked about unrelated topics, gently redirect to health-related discussion
6. Keep responses concise but thorough (2-4 paragraphs max)
7. Use bullet points when listing information

Respond now:
""")


def run(question, analysis_context, patient_info, chat_history):
    """
    Run the Chat Agent.

    Args:
        question: user's question
        analysis_context: dict with full analysis data
        patient_info: patient data dict
        chat_history: list of previous chat messages

    Returns:
        str: AI response
    """
    llm = get_llm()
    chain = CHAT_PROMPT | llm

    # Format chat history
    history_str = ""
    for msg in chat_history[-6:]:  # Keep last 6 messages for context
        role = "Patient" if msg["role"] == "user" else "AI"
        history_str += f"{role}: {msg['content']}\n"

    # Format region summary
    region_summary = ""
    regions = analysis_context.get("regions", {})
    for name, info in regions.items():
        region_summary += f"{name}: {info.get('status', 'N/A')}, "

    response = chain.invoke({
        "top_findings": str(analysis_context.get("top_findings", {})),
        "neural_score": analysis_context.get("neural_score", {}).get("score", "N/A"),
        "risk_tier": analysis_context.get("neural_score", {}).get("tier", {}).get("level", "N/A"),
        "region_summary": region_summary or "Not available",
        "analysis_summary": analysis_context.get("recommendation", "Not available"),
        "age": patient_info.get("age", "N/A"),
        "gender": patient_info.get("gender", "N/A"),
        "symptoms": patient_info.get("symptoms", "None reported"),
        "question": question,
        "chat_history": history_str or "No previous messages"
    })

    return response.content
