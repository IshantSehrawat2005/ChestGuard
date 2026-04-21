# 🫁 ChestGuard NeuralScan

### AI-Powered Chest X-Ray Diagnostic Intelligence Platform

ChestGuard NeuralScan is a patent-pending, next-generation chest X-ray analysis platform that combines deep learning explainability, multi-agent diagnostic reasoning, and composite risk intelligence into a single, interactive web application.

---

## ✨ Key Innovations

### 🧠 GradCAM Visual Explainability
For each detected condition, the system generates heatmaps showing exactly WHERE on the X-ray the AI is focusing — transforming a black-box model into a transparent, trustworthy diagnostic tool.

### 🔬 Anatomical Region Intelligence
X-rays are automatically segmented into 6 anatomical zones (left/right upper/lower lungs, cardiac region, costophrenic angles) with per-region findings and health scores.

### 🤖 Multi-Agent Diagnostic Pipeline
Four specialized AI agents analyze sequentially, each building on the previous:
1. **Screening Agent** — Analyzes raw DenseNet predictions + GradCAM focus areas
2. **Correlation Agent** — Cross-references findings with patient symptoms/history
3. **Risk Stratification Agent** — Interprets NeuralScore™ and risk factors
4. **Recommendation Agent** — Produces actionable next-steps with urgency levels

### 📊 NeuralScore™ Composite Risk
A novel 0-100 risk scoring algorithm combining:
- Imaging severity (40%)
- Age risk factor (15%)
- Smoking history (15%)
- Symptom correlation (20%)
- Comorbidity multiplier (10%)

### ⏳ Temporal Progression Tracking
Upload multiple X-rays over time to track disease progression with delta analysis and automated alerts.

### 💬 Contextual AI Chat
Chat agent with full analysis context that can reference specific findings and regions.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Flask (Python) |
| Frontend | Vanilla HTML/CSS/JS |
| ML Model | DenseNet-121 (torchxrayvision) |
| Explainability | Custom GradCAM Engine |
| LLM | Groq (Llama 3.1) via LangChain |
| Charts | Chart.js |
| PDF Reports | FPDF |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ChestGuard.git
cd ChestGuard

# Install dependencies
uv sync

# Set up environment variables
# Edit .env and add your Groq API key:
# GROQ_API_KEY=your_key_here
```

### Running

```bash
uv run python server.py
```

Then open **http://localhost:5000** in your browser.

---

## 📁 Project Structure

```
ChestGuard/
├── server.py              # Flask application entry point
├── config.py              # Configuration & environment variables
├── .env                   # API keys (gitignored)
├── core/                  # Core ML & AI logic
│   ├── xray_analyzer.py   # DenseNet-121 model + prediction pipeline
│   ├── gradcam_engine.py  # GradCAM heatmap generation
│   ├── region_analyzer.py # Anatomical region segmentation
│   ├── risk_engine.py     # NeuralScore™ algorithm
│   └── temporal_tracker.py# Multi-scan progression analysis
├── agents/                # Multi-agent LLM pipeline
│   ├── screening_agent.py # Agent 1: Raw finding analysis
│   ├── correlation_agent.py# Agent 2: Symptom correlation
│   ├── risk_agent.py      # Agent 3: Risk stratification
│   ├── recommendation_agent.py # Agent 4: Recommendations
│   ├── chat_agent.py      # Conversational agent
│   └── pipeline.py        # Orchestrates all agents
├── api/                   # Flask API routes
│   ├── analysis_routes.py # X-ray analysis endpoints
│   ├── chat_routes.py     # Chat endpoints
│   ├── report_routes.py   # PDF report generation
│   └── temporal_routes.py # Temporal tracking endpoints
├── static/                # Frontend assets
│   ├── css/style.css      # Design system
│   └── js/                # Application logic
└── templates/
    └── index.html         # Single-page application
```

---

## ⚠️ Disclaimer

ChestGuard NeuralScan is an AI-assisted screening tool for **educational and research purposes only**. It is **NOT** a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional.

---

## 📄 License

© 2026 ChestGuard NeuralScan. All rights reserved. Patent Pending.
