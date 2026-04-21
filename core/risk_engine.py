"""
ChestGuard NeuralScan — NeuralScore™ Risk Engine
Composite risk scoring algorithm combining imaging + clinical data.
"""
import numpy as np


# Risk weights for the composite score
WEIGHTS = {
    "imaging_severity": 0.40,
    "age_factor": 0.15,
    "smoking_risk": 0.15,
    "symptom_correlation": 0.20,
    "comorbidity_multiplier": 0.10
}

# Condition severity mappings
CRITICAL_CONDITIONS = {
    "Pneumothorax", "Mass", "Nodule", "Lung Opacity",
    "Consolidation", "Pleural Effusion"
}

MODERATE_CONDITIONS = {
    "Atelectasis", "Cardiomegaly", "Edema", "Infiltration",
    "Pneumonia"
}

# Smoking risk multipliers
SMOKING_RISK = {
    "Never": 0.0,
    "Former Smoker": 0.4,
    "Current Smoker": 0.85
}

# Known comorbidity risk factors
COMORBIDITY_KEYWORDS = {
    "diabetes": 0.15,
    "hypertension": 0.12,
    "copd": 0.25,
    "asthma": 0.18,
    "heart disease": 0.20,
    "cancer": 0.30,
    "hiv": 0.22,
    "tuberculosis": 0.28,
    "obesity": 0.10,
    "kidney": 0.12
}


def calculate_neural_score(results, patient_info):
    """
    Calculate the NeuralScore™ — a composite 0-100 risk score.

    Args:
        results: dict of {condition: probability%}
        patient_info: dict with age, gender, symptoms, smoking, conditions

    Returns:
        dict with score, tier, breakdown, and recommendations
    """
    # 1. Imaging Severity Score (0-100)
    imaging_score = _calculate_imaging_severity(results)

    # 2. Age Factor Score (0-100)
    age_score = _calculate_age_factor(patient_info.get("age", 30))

    # 3. Smoking Risk Score (0-100)
    smoking_score = _calculate_smoking_risk(
        patient_info.get("smoking", "Never"),
        patient_info.get("age", 30)
    )

    # 4. Symptom Correlation Score (0-100)
    symptom_score = _calculate_symptom_correlation(
        results, patient_info.get("symptoms", "")
    )

    # 5. Comorbidity Score (0-100)
    comorbidity_score = _calculate_comorbidity_risk(
        patient_info.get("conditions", "")
    )

    # Weighted composite
    neural_score = (
        WEIGHTS["imaging_severity"] * imaging_score +
        WEIGHTS["age_factor"] * age_score +
        WEIGHTS["smoking_risk"] * smoking_score +
        WEIGHTS["symptom_correlation"] * symptom_score +
        WEIGHTS["comorbidity_multiplier"] * comorbidity_score
    )

    neural_score = round(min(100, max(0, neural_score)), 1)

    # Determine tier
    tier = _get_risk_tier(neural_score)

    return {
        "score": neural_score,
        "tier": tier,
        "breakdown": {
            "imaging_severity": {
                "score": round(imaging_score, 1),
                "weight": WEIGHTS["imaging_severity"],
                "contribution": round(WEIGHTS["imaging_severity"] * imaging_score, 1),
                "label": "Imaging Findings"
            },
            "age_factor": {
                "score": round(age_score, 1),
                "weight": WEIGHTS["age_factor"],
                "contribution": round(WEIGHTS["age_factor"] * age_score, 1),
                "label": "Age Risk Factor"
            },
            "smoking_risk": {
                "score": round(smoking_score, 1),
                "weight": WEIGHTS["smoking_risk"],
                "contribution": round(WEIGHTS["smoking_risk"] * smoking_score, 1),
                "label": "Smoking History"
            },
            "symptom_correlation": {
                "score": round(symptom_score, 1),
                "weight": WEIGHTS["symptom_correlation"],
                "contribution": round(WEIGHTS["symptom_correlation"] * symptom_score, 1),
                "label": "Symptom Correlation"
            },
            "comorbidity_multiplier": {
                "score": round(comorbidity_score, 1),
                "weight": WEIGHTS["comorbidity_multiplier"],
                "contribution": round(WEIGHTS["comorbidity_multiplier"] * comorbidity_score, 1),
                "label": "Comorbidities"
            }
        },
        "action": _get_recommended_action(tier)
    }


def _calculate_imaging_severity(results):
    """Score based on detected conditions and their probabilities."""
    score = 0
    top_5 = list(results.items())[:5]

    for condition, prob in top_5:
        if condition == "No Finding":
            continue

        weight = 1.0
        if condition in CRITICAL_CONDITIONS:
            weight = 1.5
        elif condition in MODERATE_CONDITIONS:
            weight = 1.2

        # Non-linear scaling — high probabilities contribute more
        contribution = (prob / 100) ** 0.8 * weight * 30
        score += contribution

    return min(100, score)


def _calculate_age_factor(age):
    """Age-based risk factor."""
    try:
        age = int(age)
    except (ValueError, TypeError):
        return 20

    if age < 18:
        return 15
    elif age < 30:
        return 10
    elif age < 45:
        return 20
    elif age < 60:
        return 40
    elif age < 75:
        return 65
    else:
        return 85


def _calculate_smoking_risk(smoking_status, age):
    """Smoking-related risk score."""
    base_risk = SMOKING_RISK.get(smoking_status, 0) * 100

    try:
        age = int(age)
        if smoking_status == "Current Smoker" and age > 50:
            base_risk = min(100, base_risk * 1.3)
    except (ValueError, TypeError):
        pass

    return base_risk


def _calculate_symptom_correlation(results, symptoms):
    """How well do symptoms correlate with imaging findings."""
    if not symptoms or symptoms == "None reported":
        return 10

    symptoms_lower = symptoms.lower()
    score = 0

    # Symptom-condition correlation pairs
    correlations = {
        "cough": ["Pneumonia", "Consolidation", "Infiltration", "Mass"],
        "fever": ["Pneumonia", "Consolidation", "Infiltration"],
        "breathing": ["Pneumothorax", "Pleural Effusion", "Edema", "Consolidation"],
        "chest pain": ["Pneumothorax", "Cardiomegaly", "Pleural Effusion"],
        "fatigue": ["Cardiomegaly", "Edema", "Pleural Effusion"],
        "weight loss": ["Mass", "Nodule", "Lung Opacity"]
    }

    matched = 0
    total_checks = 0

    for symptom, related_conditions in correlations.items():
        if symptom in symptoms_lower:
            total_checks += 1
            for condition in related_conditions:
                if condition in results and results[condition] > 40:
                    matched += 1
                    break

    if total_checks > 0:
        correlation_ratio = matched / total_checks
        # High correlation means symptoms match findings = higher concern
        score = correlation_ratio * 70 + 20
    else:
        score = 15

    # More symptoms = generally higher concern
    symptom_count = len([s for s in symptoms.split(",") if s.strip()])
    score += min(30, symptom_count * 8)

    return min(100, score)


def _calculate_comorbidity_risk(conditions):
    """Risk from pre-existing conditions."""
    if not conditions or conditions == "None reported":
        return 0

    conditions_lower = conditions.lower()
    total_risk = 0

    for keyword, risk in COMORBIDITY_KEYWORDS.items():
        if keyword in conditions_lower:
            total_risk += risk * 100

    return min(100, total_risk)


def _get_risk_tier(score):
    """Categorize the risk score into a tier."""
    if score <= 25:
        return {"level": "Low", "color": "#10b981", "icon": "shield-check"}
    elif score <= 50:
        return {"level": "Moderate", "color": "#f59e0b", "icon": "alert-triangle"}
    elif score <= 75:
        return {"level": "High", "color": "#f97316", "icon": "alert-circle"}
    else:
        return {"level": "Critical", "color": "#ef4444", "icon": "alert-octagon"}


def _get_recommended_action(tier):
    """Get recommended action based on risk tier."""
    actions = {
        "Low": "Routine check-up recommended within 6 months. Maintain healthy lifestyle.",
        "Moderate": "Schedule a consultation with a pulmonologist within 2 weeks. Additional testing may be needed.",
        "High": "Seek medical attention within 48 hours. Further diagnostic imaging and blood work recommended.",
        "Critical": "Seek immediate medical attention. Emergency evaluation may be necessary."
    }
    return actions.get(tier["level"], actions["Moderate"])
