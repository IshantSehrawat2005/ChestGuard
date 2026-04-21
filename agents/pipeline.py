"""
ChestGuard NeuralScan — Multi-Agent Pipeline Orchestrator
Runs all 4 diagnostic agents sequentially, passing context forward.
"""
from agents import screening_agent, correlation_agent, risk_agent, recommendation_agent


def run_full_pipeline(results, top_findings, heatmap_conditions,
                      patient_info, neural_score_data, region_data):
    """
    Execute the complete multi-agent diagnostic pipeline.

    Pipeline:
        Agent 1 (Screening) → Agent 2 (Correlation) →
        Agent 3 (Risk) → Agent 4 (Recommendations)

    Each agent receives the output of the previous agent(s).

    Returns:
        dict with all agent outputs and the pipeline status
    """
    pipeline_results = {
        "agents": [],
        "status": "running",
        "errors": []
    }

    # ── Agent 1: Screening ──
    try:
        screening_result = screening_agent.run(
            results, top_findings, heatmap_conditions
        )
        pipeline_results["agents"].append(screening_result)
    except Exception as e:
        screening_result = {"output": f"Screening analysis unavailable: {str(e)}"}
        pipeline_results["agents"].append({
            "agent": "Screening Specialist",
            "icon": "🔬",
            "output": screening_result["output"],
            "status": "error"
        })
        pipeline_results["errors"].append(f"Screening Agent: {str(e)}")

    # ── Agent 2: Correlation ──
    try:
        correlation_result = correlation_agent.run(
            screening_result["output"], patient_info
        )
        pipeline_results["agents"].append(correlation_result)
    except Exception as e:
        correlation_result = {"output": f"Correlation analysis unavailable: {str(e)}"}
        pipeline_results["agents"].append({
            "agent": "Correlation Specialist",
            "icon": "🔗",
            "output": correlation_result["output"],
            "status": "error"
        })
        pipeline_results["errors"].append(f"Correlation Agent: {str(e)}")

    # ── Agent 3: Risk Stratification ──
    try:
        risk_result = risk_agent.run(
            screening_result["output"],
            correlation_result["output"],
            neural_score_data,
            region_data
        )
        pipeline_results["agents"].append(risk_result)
    except Exception as e:
        risk_result = {"output": f"Risk assessment unavailable: {str(e)}"}
        pipeline_results["agents"].append({
            "agent": "Risk Stratification",
            "icon": "📊",
            "output": risk_result["output"],
            "status": "error"
        })
        pipeline_results["errors"].append(f"Risk Agent: {str(e)}")

    # ── Agent 4: Recommendations ──
    try:
        recommendation_result = recommendation_agent.run(
            screening_result["output"],
            correlation_result["output"],
            risk_result["output"],
            patient_info,
            neural_score_data
        )
        pipeline_results["agents"].append(recommendation_result)
    except Exception as e:
        recommendation_result = {"output": f"Recommendations unavailable: {str(e)}"}
        pipeline_results["agents"].append({
            "agent": "Clinical Recommendations",
            "icon": "💡",
            "output": recommendation_result["output"],
            "status": "error"
        })
        pipeline_results["errors"].append(f"Recommendation Agent: {str(e)}")

    pipeline_results["status"] = "complete"
    pipeline_results["recommendation"] = recommendation_result["output"]

    return pipeline_results
