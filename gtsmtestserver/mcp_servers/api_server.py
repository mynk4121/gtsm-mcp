from mcp.server.fastmcp import FastMCP
import httpx
import os
import time

# =========================================================
# FIXED: HARDSET API BASE URL (NO ENV AMBIGUITY)
# =========================================================

mcp = FastMCP("gtsm-api")
API_BASE_URL = "http://127.0.0.1:8000"
# =========================================================
# SAFE HTTP CLIENT WITH RETRY + TIMEOUT
# =========================================================

def api_request(method: str, path: str, retries: int = 3, **kwargs):
    url = f"{API_BASE_URL}{path}"

    last_error = None

    for attempt in range(retries):
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            last_error = e
            time.sleep(0.5)  # small backoff

    # final failure
    raise RuntimeError(f"API request failed after retries: {last_error}")


# =========================================================
# USER CRUD TOOLS
# =========================================================
@mcp.tool()
def api_find_user_by_name(name: str) -> str:
    try:
        users = api_request("GET", "/users")

        matches = [
            u for u in users
            if name.lower() in u["name"].lower()
        ]

        if not matches:
            return "NO_MATCH"

        result = []

        for u in matches:
            result.append(
                f"{u['id']}|{u['name']}|{u['email']}|{u['department']}"
            )

        return "\n".join(result)

    except Exception as e:
        return f"API ERROR (find_user_by_name): {e}"
        
@mcp.tool()
def api_list_users() -> str:
    try:
        users = api_request("GET", "/users")

        if not users:
            return "No users found."

        result = "Users (CRUD DB via API):\n"
        for u in users:
            result += f"  - [{u['id']}] {u['name']} ({u['email']}) - {u['department']}\n"

        return result

    except Exception as e:
        return f"API ERROR (list_users): {e}"


@mcp.tool()
def api_get_user(user_id: int) -> str:
    try:
        user = api_request("GET", f"/users/{user_id}")
        return f"User [{user['id']}]: {user['name']} ({user['email']}) - {user['department']}"
    except Exception as e:
        return f"API ERROR (get_user): {e}"


@mcp.tool()
def api_create_user(name: str, email: str, department: str) -> str:
    try:
        user = api_request(
            "POST",
            "/users",
            json={"name": name, "email": email, "department": department}
        )
        return f"Created user [{user['id']}]: {user['name']} ({user['email']}) - {user['department']}"
    except Exception as e:
        return f"API ERROR (create_user): {e}"


@mcp.tool()
def api_update_user(user_id: int, name: str | None = None, email: str | None = None, department: str | None = None) -> str:
    try:
        updates = {}
        if name: updates["name"] = name
        if email: updates["email"] = email
        if department: updates["department"] = department

        user = api_request("PUT", f"/users/{user_id}", json=updates)

        return f"Updated user [{user['id']}]: {user['name']} ({user['email']}) - {user['department']}"

    except Exception as e:
        return f"API ERROR (update_user): {e}"


@mcp.tool()
def api_delete_user(user_id: int) -> str:
    try:
        result = api_request("DELETE", f"/users/{user_id}")
        return result.get("message", f"User {user_id} deleted")
    except Exception as e:
        return f"API ERROR (delete_user): {e}"


# =========================================================
# INCIDENT CRUD TOOLS
# =========================================================

@mcp.tool()
def api_list_incidents() -> str:
    try:
        incidents = api_request("GET", "/incidents")

        if not incidents:
            return "No incidents found."

        result = "Incidents (CRUD DB via API):\n"
        for inc in incidents:
            result += f"  - [{inc['id']}] {inc['number']}: {inc['description']} [{inc['status']}]\n"

        return result

    except Exception as e:
        return f"API ERROR (list_incidents): {e}"


@mcp.tool()
def api_get_incident(incident_id: int) -> str:
    try:
        inc = api_request("GET", f"/incidents/{incident_id}")
        return f"Incident [{inc['id']}]: {inc['number']} - {inc['description']} [{inc['status']}]"
    except Exception as e:
        return f"API ERROR (get_incident): {e}"


@mcp.tool()
def api_create_incident(number: str, description: str, status: str = "open") -> str:
    try:
        inc = api_request(
            "POST",
            "/incidents",
            json={"number": number, "description": description, "status": status}
        )
        return f"Created incident [{inc['id']}]: {inc['number']} - {inc['description']} [{inc['status']}]"
    except Exception as e:
        return f"API ERROR (create_incident): {e}"


@mcp.tool()
def api_update_incident(incident_id: int, number: str | None = None, description: str | None = None, status: str | None = None) -> str:
    try:
        updates = {}
        if number: updates["number"] = number
        if description: updates["description"] = description
        if status: updates["status"] = status

        inc = api_request("PUT", f"/incidents/{incident_id}", json=updates)
        return f"Updated incident [{inc['id']}]: {inc['number']} - {inc['description']} [{inc['status']}]"

    except Exception as e:
        return f"API ERROR (update_incident): {e}"


@mcp.tool()
def api_delete_incident(incident_id: int) -> str:
    try:
        result = api_request("DELETE", f"/incidents/{incident_id}")
        return result.get("message", f"Incident {incident_id} deleted")
    except Exception as e:
        return f"API ERROR (delete_incident): {e}"


@mcp.tool()
def api_search_incidents(status: str) -> str:
    try:
        incidents = api_request("GET", "/incidents")
        filtered = [i for i in incidents if i["status"] == status]

        if not filtered:
            return f"No incidents with status '{status}'"

        result = f"Incidents [{status}]:\n"
        for inc in filtered:
            result += f"  - [{inc['id']}] {inc['number']} - {inc['description']}\n"

        return result

    except Exception as e:
        return f"API ERROR (search_incidents): {e}"