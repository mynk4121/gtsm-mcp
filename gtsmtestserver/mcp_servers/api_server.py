"""
MCP Server 2: REST API Client (CRUD Operations)
Tools that call the FastAPI REST endpoints for CRUD operations
"""
from mcp.server.fastmcp import FastMCP
import httpx
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

mcp = FastMCP("gtsm-api")


def api_request(method: str, path: str, **kwargs):
    """Make HTTP request to REST API."""
    url = f"{API_BASE_URL}{path}"
    with httpx.Client() as client:
        response = client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()


# ============================================
# USER CRUD TOOLS
# ============================================

@mcp.tool()
def api_list_users() -> str:
    """List all users via REST API (CRUD DB)."""
    try:
        users = api_request("GET", "/users")
        if not users:
            return "No users found."
        result = "Users (CRUD DB via API):\n"
        for u in users:
            result += f"  - [{u['id']}] {u['name']} ({u['email']}) - {u['department']}\n"
        return result
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def api_get_user(user_id: int) -> str:
    """Get a specific user by ID via REST API.

    Args:
        user_id: The user's ID number
    """
    try:
        user = api_request("GET", f"/users/{user_id}")
        return f"User (CRUD DB) [{user['id']}]: {user['name']} ({user['email']}) - {user['department']}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def api_create_user(name: str, email: str, department: str) -> str:
    """Create a new user via REST API.

    Args:
        name: User's full name
        email: User's email address
        department: User's department
    """
    try:
        user = api_request("POST", "/users", json={
            "name": name,
            "email": email,
            "department": department
        })
        return f"Created user (CRUD DB) [{user['id']}]: {user['name']} ({user['email']}) - {user['department']}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def api_update_user(user_id: int, name: str | None = None, email: str | None = None, department: str | None = None) -> str:
    """Update a user via REST API.

    Args:
        user_id: The user's ID number
        name: New name (optional)
        email: New email (optional)
        department: New department (optional)
    """
    try:
        updates = {}
        if name is not None:
            updates["name"] = name
        if email is not None:
            updates["email"] = email
        if department is not None:
            updates["department"] = department
        user = api_request("PUT", f"/users/{user_id}", json=updates)
        return f"Updated user (CRUD DB) [{user['id']}]: {user['name']} ({user['email']}) - {user['department']}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def api_delete_user(user_id: int) -> str:
    """Delete a user via REST API.

    Args:
        user_id: The user's ID number
    """
    try:
        result = api_request("DELETE", f"/users/{user_id}")
        return result.get("message", f"User {user_id} deleted")
    except Exception as e:
        return f"Error: {e}"


# ============================================
# INCIDENT CRUD TOOLS
# ============================================

@mcp.tool()
def api_list_incidents() -> str:
    """List all incidents via REST API (CRUD DB)."""
    try:
        incidents = api_request("GET", "/incidents")
        if not incidents:
            return "No incidents found."
        result = "Incidents (CRUD DB via API):\n"
        for inc in incidents:
            result += f"  - [{inc['id']}] {inc['number']}: {inc['description']} [{inc['status']}]\n"
        return result
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def api_get_incident(incident_id: int) -> str:
    """Get a specific incident by ID via REST API.

    Args:
        incident_id: The incident's ID number
    """
    try:
        inc = api_request("GET", f"/incidents/{incident_id}")
        return f"Incident (CRUD DB) [{inc['id']}]: {inc['number']} - {inc['description']} [{inc['status']}]"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def api_create_incident(number: str, description: str, status: str = "open") -> str:
    """Create a new incident via REST API.

    Args:
        number: Incident number (e.g., INC001)
        description: Description of the issue
        status: Initial status (open, in_progress, resolved)
    """
    try:
        inc = api_request("POST", "/incidents", json={
            "number": number,
            "description": description,
            "status": status
        })
        return f"Created incident (CRUD DB) [{inc['id']}]: {inc['number']} - {inc['description']} [{inc['status']}]"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def api_update_incident(incident_id: int, number: str | None = None, description: str | None = None, status: str | None = None) -> str:
    """Update an incident via REST API.

    Args:
        incident_id: The incident's ID number
        number: New incident number (optional)
        description: New description (optional)
        status: New status (optional: open, in_progress, resolved)
    """
    try:
        updates = {}
        if number is not None:
            updates["number"] = number
        if description is not None:
            updates["description"] = description
        if status is not None:
            updates["status"] = status
        inc = api_request("PUT", f"/incidents/{incident_id}", json=updates)
        return f"Updated incident (CRUD DB) [{inc['id']}]: {inc['number']} - {inc['description']} [{inc['status']}]"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def api_delete_incident(incident_id: int) -> str:
    """Delete an incident via REST API.

    Args:
        incident_id: The incident's ID number
    """
    try:
        result = api_request("DELETE", f"/incidents/{incident_id}")
        return result.get("message", f"Incident {incident_id} deleted")
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def api_search_incidents(status: str) -> str:
    """Search incidents by status via REST API.

    Args:
        status: Incident status (open, in_progress, resolved)
    """
    try:
        incidents = api_request("GET", "/incidents")
        filtered = [inc for inc in incidents if inc["status"] == status]
        if not filtered:
            return f"No incidents with status '{status}' found."
        result = f"Incidents with status '{status}' (CRUD DB):\n"
        for inc in filtered:
            result += f"  - [{inc['id']}] {inc['number']}: {inc['description']} [{inc['status']}]\n"
        return result
    except Exception as e:
        return f"Error: {e}"
