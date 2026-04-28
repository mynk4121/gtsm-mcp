"""
MCP Server 1: Direct Database Access (READ-ONLY)
Tools that read from the read-only database
"""
from mcp.server.fastmcp import FastMCP
import sqlite3
import os

# Set working directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# READ-ONLY database path
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "readonly.db")

mcp = FastMCP("gtsm-db")


def get_connection():
    return sqlite3.connect(DB_PATH)


@mcp.tool()
def db_list_users() -> str:
    """List all users directly from READ-ONLY database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, department FROM users")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No users found."

    result = "Users (READ-ONLY DB):\n"
    for row in rows:
        result += f"  - {row[1]} ({row[2]}) - {row[3]}\n"
    return result


@mcp.tool()
def db_list_incidents() -> str:
    """List all incidents directly from READ-ONLY database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, number, description, status FROM incidents")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No incidents found."

    result = "Incidents (READ-ONLY DB):\n"
    for row in rows:
        result += f"  - {row[1]}: {row[2]} [{row[3]}]\n"
    return result


@mcp.tool()
def db_search_incidents(status: str) -> str:
    """Search incidents by status directly from READ-ONLY database.

    Args:
        status: Incident status (open, in_progress, resolved)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, number, description, status FROM incidents WHERE status = ?", (status,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return f"No incidents with status '{status}' found."

    result = f"Incidents with status '{status}' (READ-ONLY DB):\n"
    for row in rows:
        result += f"  - {row[1]}: {row[2]} [{row[3]}]\n"
    return result
