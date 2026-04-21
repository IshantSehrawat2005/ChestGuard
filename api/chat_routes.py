"""
ChestGuard NeuralScan — Chat API Routes
"""
from flask import Blueprint, request, jsonify, session
from agents.chat_agent import run as chat_run
from database import save_chat_message

chat_bp = Blueprint("chat", __name__)

# In-memory chat history per session
_chat_histories = {}


@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    """
    Chat endpoint for follow-up questions.
    Accepts: JSON with 'message' field.
    Returns: AI response with context.
    """
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400

    message = data["message"].strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    session_id = session.get("session_id", "default")

    # Get or create chat history
    if session_id not in _chat_histories:
        _chat_histories[session_id] = []

    chat_history = _chat_histories[session_id]

    # Get analysis context from session
    analysis_context = session.get("analysis_context", {})
    patient_info = session.get("patient_info", {})

    if not analysis_context:
        return jsonify({
            "response": "I don't have any X-ray analysis context yet. Please upload and analyze an X-ray first, then I can answer your questions about the results.",
            "has_context": False
        })

    # Add user message to history
    chat_history.append({"role": "user", "content": message})

    try:
        # Get AI response
        response = chat_run(message, analysis_context, patient_info, chat_history)

        # Add AI response to history
        chat_history.append({"role": "assistant", "content": response})

        # Save to local database
        scan_id = session.get("current_scan_id")
        if scan_id:
            try:
                save_chat_message(scan_id, "user", message)
                save_chat_message(scan_id, "assistant", response)
            except Exception as db_err:
                print(f"Chat DB save error: {db_err}")

        # Keep only last 20 messages
        if len(chat_history) > 20:
            _chat_histories[session_id] = chat_history[-20:]

        return jsonify({
            "response": response,
            "has_context": True
        })

    except Exception as e:
        return jsonify({
            "error": f"Chat error: {str(e)}",
            "response": "I'm having trouble processing your question. Please try again."
        }), 500


@chat_bp.route("/api/chat/clear", methods=["POST"])
def clear_chat():
    """Clear chat history for current session."""
    session_id = session.get("session_id", "default")
    if session_id in _chat_histories:
        _chat_histories[session_id] = []
    return jsonify({"status": "cleared"})
