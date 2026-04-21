"""
ChestGuard NeuralScan — Local SQLite Database
Persists all patient data, scan results, and analysis history locally.
"""
import sqlite3
import json
import os
import shutil
from datetime import datetime
from config import UPLOAD_FOLDER

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chestguard.db")
IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_scans")


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize the database schema."""
    os.makedirs(IMAGES_DIR, exist_ok=True)

    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT DEFAULT '',
            age INTEGER,
            gender TEXT,
            symptoms TEXT,
            smoking_history TEXT,
            pre_existing_conditions TEXT,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            xray_filename TEXT,
            xray_original_name TEXT,
            predictions JSON,
            top_findings JSON,
            neural_score REAL,
            risk_tier TEXT,
            neural_score_data JSON,
            regions_data JSON,
            pipeline_results JSON,
            heatmaps_generated INTEGER DEFAULT 0,
            scan_label TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id INTEGER,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_scans_patient ON scans(patient_id);
        CREATE INDEX IF NOT EXISTS idx_scans_created ON scans(created_at);
        CREATE INDEX IF NOT EXISTS idx_chat_scan ON chat_messages(scan_id);
    """)

    conn.commit()
    conn.close()


# ═══════════════════════════════════════════
# PATIENT OPERATIONS
# ═══════════════════════════════════════════

def save_patient(patient_info):
    """
    Save or update a patient record.
    Returns the patient ID.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO patients (name, age, gender, symptoms, smoking_history, pre_existing_conditions)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        patient_info.get("name", ""),
        patient_info.get("age", 0),
        patient_info.get("gender", ""),
        patient_info.get("symptoms", ""),
        patient_info.get("smoking", ""),
        patient_info.get("conditions", "")
    ))

    patient_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return patient_id


def get_all_patients():
    """Get all patients with their scan count."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.*,
               COUNT(s.id) as scan_count,
               MAX(s.created_at) as last_scan_date
        FROM patients p
        LEFT JOIN scans s ON s.patient_id = p.id
        GROUP BY p.id
        ORDER BY p.created_at DESC
    """)

    patients = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return patients


def get_patient(patient_id):
    """Get a single patient by ID."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def delete_patient(patient_id):
    """Delete a patient and all associated scans/chats."""
    # Also delete saved images
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT xray_filename FROM scans WHERE patient_id = ?", (patient_id,))
    for row in cursor.fetchall():
        if row["xray_filename"]:
            img_path = os.path.join(IMAGES_DIR, row["xray_filename"])
            if os.path.exists(img_path):
                os.remove(img_path)

    cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════
# SCAN OPERATIONS
# ═══════════════════════════════════════════

def save_scan(patient_id, scan_data, xray_file_bytes=None, original_filename=""):
    """
    Save a scan with all analysis results.
    Optionally saves the X-ray image file locally.
    Returns the scan ID.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Save X-ray image to disk
    xray_filename = ""
    if xray_file_bytes:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = os.path.splitext(original_filename)[1] if original_filename else ".png"
        xray_filename = f"scan_{patient_id}_{timestamp}{ext}"
        img_path = os.path.join(IMAGES_DIR, xray_filename)
        with open(img_path, "wb") as f:
            f.write(xray_file_bytes)

    cursor.execute("""
        INSERT INTO scans (
            patient_id, xray_filename, xray_original_name,
            predictions, top_findings,
            neural_score, risk_tier, neural_score_data,
            regions_data, pipeline_results,
            heatmaps_generated, scan_label
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        patient_id,
        xray_filename,
        original_filename,
        json.dumps(scan_data.get("predictions", {})),
        json.dumps(scan_data.get("top_findings", {})),
        scan_data.get("neural_score", {}).get("score", 0),
        scan_data.get("neural_score", {}).get("tier", {}).get("level", "Unknown"),
        json.dumps(scan_data.get("neural_score", {})),
        json.dumps(scan_data.get("regions", {})),
        json.dumps(scan_data.get("pipeline", {})),
        1 if scan_data.get("heatmaps") else 0,
        scan_data.get("scan_label", "")
    ))

    scan_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return scan_id


def get_patient_scans(patient_id):
    """Get all scans for a patient, ordered by date."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, patient_id, xray_filename, xray_original_name,
               neural_score, risk_tier, scan_label, created_at,
               top_findings, predictions
        FROM scans
        WHERE patient_id = ?
        ORDER BY created_at DESC
    """, (patient_id,))

    scans = []
    for row in cursor.fetchall():
        scan = dict(row)
        scan["top_findings"] = json.loads(scan["top_findings"]) if scan["top_findings"] else {}
        scan["predictions"] = json.loads(scan["predictions"]) if scan["predictions"] else {}
        scans.append(scan)

    conn.close()
    return scans


def get_scan(scan_id):
    """Get a full scan record with all data."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    scan = dict(row)
    # Parse JSON fields
    for field in ["predictions", "top_findings", "neural_score_data", "regions_data", "pipeline_results"]:
        if scan.get(field):
            try:
                scan[field] = json.loads(scan[field])
            except (json.JSONDecodeError, TypeError):
                pass

    return scan


def get_all_scans():
    """Get all scans across all patients (for dashboard)."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.id, s.patient_id, s.neural_score, s.risk_tier,
               s.scan_label, s.created_at, s.xray_original_name,
               p.name as patient_name, p.age, p.gender
        FROM scans s
        JOIN patients p ON p.id = s.patient_id
        ORDER BY s.created_at DESC
        LIMIT 50
    """)

    scans = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return scans


def delete_scan(scan_id):
    """Delete a single scan and its image file."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT xray_filename FROM scans WHERE id = ?", (scan_id,))
    row = cursor.fetchone()
    if row and row["xray_filename"]:
        img_path = os.path.join(IMAGES_DIR, row["xray_filename"])
        if os.path.exists(img_path):
            os.remove(img_path)

    cursor.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════
# CHAT OPERATIONS
# ═══════════════════════════════════════════

def save_chat_message(scan_id, role, content):
    """Save a chat message associated with a scan."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO chat_messages (scan_id, role, content)
        VALUES (?, ?, ?)
    """, (scan_id, role, content))

    conn.commit()
    conn.close()


def get_chat_history(scan_id):
    """Get chat history for a specific scan."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role, content, created_at
        FROM chat_messages
        WHERE scan_id = ?
        ORDER BY created_at ASC
    """, (scan_id,))

    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return messages


# ═══════════════════════════════════════════
# STATS
# ═══════════════════════════════════════════

def get_dashboard_stats():
    """Get aggregate statistics for the dashboard."""
    conn = get_db()
    cursor = conn.cursor()

    stats = {}

    cursor.execute("SELECT COUNT(*) as count FROM patients")
    stats["total_patients"] = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM scans")
    stats["total_scans"] = cursor.fetchone()["count"]

    cursor.execute("SELECT AVG(neural_score) as avg FROM scans WHERE neural_score > 0")
    row = cursor.fetchone()
    stats["avg_neural_score"] = round(row["avg"], 1) if row["avg"] else 0

    cursor.execute("""
        SELECT risk_tier, COUNT(*) as count
        FROM scans
        GROUP BY risk_tier
    """)
    stats["risk_distribution"] = {row["risk_tier"]: row["count"] for row in cursor.fetchall()}

    conn.close()
    return stats
