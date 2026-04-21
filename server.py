"""
ChestGuard NeuralScan — Flask Application Server
"""
import os
from flask import Flask, render_template, session
from config import FLASK_SECRET_KEY, UPLOAD_FOLDER

from api.analysis_routes import analysis_bp
from api.chat_routes import chat_bp
from api.report_routes import report_bp
from api.temporal_routes import temporal_bp
from api.history_routes import history_bp
from database import init_db


def create_app():
    app = Flask(__name__)
    app.secret_key = FLASK_SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

    # Create uploads directory
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Initialize local database
    init_db()

    # Register blueprints
    app.register_blueprint(analysis_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(temporal_bp)
    app.register_blueprint(history_bp)

    # Main page
    @app.route("/")
    def index():
        return render_template("index.html")

    # Health check
    @app.route("/api/health")
    def health():
        return {"status": "ok", "app": "ChestGuard NeuralScan"}

    return app


if __name__ == "__main__":
    app = create_app()
    print("\n" + "=" * 60)
    print("  ChestGuard NeuralScan — Starting Server")
    print("  Open: http://localhost:5000")
    print("=" * 60 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
