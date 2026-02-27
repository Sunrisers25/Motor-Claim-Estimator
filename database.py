"""
database.py
-----------
Initializes and manages the local SQLite database.

Tables:
  - parts_cost    : base replacement costs for each part type
  - claim_history : Feature 17 — persisted claim records for analytics
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "claim_estimator.db")

# ── Parts base costs (in INR ₹) ───────────────────────────────────────────────
PARTS_DATA = {
    "bumper":     6000,
    "headlight":  3500,
    "door":       8000,
    "windshield": 7000,
    "hood":       9000,
    "scratch":    1500,
    "dent":       2500,
}

FIXED_LABOR_COST = 2000   # INR per damaged part


# ──────────────────────────────────────────────────────────────────────────────
# Connection
# ──────────────────────────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """Return a connection to the local SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # allows dict-like access
    return conn


# ──────────────────────────────────────────────────────────────────────────────
# Schema initialization
# ──────────────────────────────────────────────────────────────────────────────

def initialize_db() -> None:
    """Create all tables and seed default data. Safe to call multiple times."""
    conn = get_connection()
    cursor = conn.cursor()

    # Parts cost table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parts_cost (
            part_name   TEXT PRIMARY KEY,
            base_cost   INTEGER NOT NULL
        )
    """)
    for part, cost in PARTS_DATA.items():
        cursor.execute("""
            INSERT INTO parts_cost (part_name, base_cost)
            VALUES (?, ?)
            ON CONFLICT(part_name) DO UPDATE SET base_cost = excluded.base_cost
        """, (part, cost))

    # Claim history table (Feature 17)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS claim_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id        TEXT    NOT NULL,
            customer_name   TEXT,
            policy_number   TEXT,
            vehicle_reg     TEXT,
            vehicle_make    TEXT,
            car_type        TEXT,
            total_cost      REAL    NOT NULL,
            decision        TEXT    NOT NULL,
            timestamp       TEXT    NOT NULL,
            parts_json      TEXT,           -- JSON array of part breakdown
            num_parts       INTEGER
        )
    """)

    conn.commit()
    conn.close()


# ──────────────────────────────────────────────────────────────────────────────
# Parts queries
# ──────────────────────────────────────────────────────────────────────────────

def get_part_cost(part_name: str) -> int:
    """Return base replacement cost for a part. Defaults to 5000 if unknown."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT base_cost FROM parts_cost WHERE part_name = ?", (part_name.lower(),))
    row = cursor.fetchone()
    conn.close()
    return row["base_cost"] if row else 5000


def get_all_parts() -> dict:
    """Return all parts and their base costs as a plain dict."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT part_name, base_cost FROM parts_cost")
    rows = cursor.fetchall()
    conn.close()
    return {row["part_name"]: row["base_cost"] for row in rows}


# ──────────────────────────────────────────────────────────────────────────────
# Claim history (Feature 17)
# ──────────────────────────────────────────────────────────────────────────────

def save_claim(
    claim_id:      str,
    total_cost:    float,
    decision:      str,
    customer_name: str = "",
    policy_number: str = "",
    vehicle_reg:   str = "",
    vehicle_make:  str = "",
    car_type:      str = "Sedan",
    parts:         Optional[list] = None,
) -> None:
    """Persist a completed claim to the claim_history table."""
    conn = get_connection()
    cursor = conn.cursor()

    parts_json = json.dumps(parts or [])
    num_parts  = len(parts) if parts else 0
    timestamp  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO claim_history
            (claim_id, customer_name, policy_number, vehicle_reg, vehicle_make,
             car_type, total_cost, decision, timestamp, parts_json, num_parts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        claim_id, customer_name, policy_number, vehicle_reg, vehicle_make,
        car_type, total_cost, decision, timestamp, parts_json, num_parts,
    ))
    conn.commit()
    conn.close()


def get_all_claims() -> List[Dict]:
    """Return all saved claims as a list of dicts for the analytics dashboard."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT claim_id, customer_name, policy_number, vehicle_reg, vehicle_make,
               car_type, total_cost, decision, timestamp, num_parts
        FROM claim_history
        ORDER BY timestamp DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_claim_stats() -> Dict:
    """
    Return aggregate stats for the analytics dashboard:
      total_claims, avg_cost, approval_rate, most_damaged_part,
      decision_breakdown (dict), severity_distribution (dict)
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt, AVG(total_cost) as avg FROM claim_history")
    row = cursor.fetchone()
    total  = row["cnt"]    if row else 0
    avg_c  = row["avg"]    if row and row["avg"] else 0.0

    if total == 0:
        conn.close()
        return {
            "total_claims": 0, "avg_cost": 0.0,
            "approval_rate": 0.0, "most_damaged_part": "N/A",
            "decision_breakdown": {}, "severity_counts": {},
        }

    # Decision breakdown
    cursor.execute("""
        SELECT decision, COUNT(*) as cnt
        FROM claim_history GROUP BY decision
    """)
    dec_rows = cursor.fetchall()
    decision_breakdown = {r["decision"]: r["cnt"] for r in dec_rows}

    # Approval rate
    approved = sum(v for k, v in decision_breakdown.items() if "Approved" in k)
    approval_rate = (approved / total) * 100

    # Most damaged part from parts_json
    cursor.execute("SELECT parts_json FROM claim_history WHERE parts_json IS NOT NULL")
    part_counts: Dict[str, int] = {}
    for (pj,) in cursor.fetchall():
        try:
            for p in json.loads(pj):
                name = p.get("part_name", "unknown")
                part_counts[name] = part_counts.get(name, 0) + 1
        except Exception:
            pass

    most_damaged = max(part_counts, key=part_counts.get) if part_counts else "N/A"

    conn.close()
    return {
        "total_claims":       total,
        "avg_cost":           round(avg_c, 2),
        "approval_rate":      round(approval_rate, 1),
        "most_damaged_part":  most_damaged,
        "decision_breakdown": decision_breakdown,
        "part_frequency":     part_counts,
    }


# Auto-initialize on import
initialize_db()
