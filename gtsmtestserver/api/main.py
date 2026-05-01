from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import os

app = FastAPI(title="GTSM API", version="1.0")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "crud.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# MODELS
# =========================

class UserCreate(BaseModel):
    name: str
    email: str
    department: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None


class IncidentCreate(BaseModel):
    number: str
    description: str
    status: str = "open"


class IncidentUpdate(BaseModel):
    number: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


# =========================
# USERS
# =========================

@app.get("/users")
def list_users():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/users/{user_id}")
def get_user(user_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "User not found")
    return dict(row)


@app.post("/users")
def create_user(user: UserCreate):
    conn = get_connection()
    cur = conn.cursor()

    next_id = cur.execute("SELECT COALESCE(MAX(id),0)+1 FROM users").fetchone()[0]

    cur.execute(
        "INSERT INTO users VALUES (?, ?, ?, ?)",
        (next_id, user.name, user.email, user.department)
    )

    conn.commit()
    conn.close()

    return {"id": next_id, **user.dict()}


@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    conn = get_connection()
    cur = conn.cursor()

    if not cur.execute("SELECT 1 FROM users WHERE id=?", (user_id,)).fetchone():
        conn.close()
        raise HTTPException(404, "User not found")

    updates, values = [], []

    if user.name:
        updates.append("name=?")
        values.append(user.name)
    if user.email:
        updates.append("email=?")
        values.append(user.email)
    if user.department:
        updates.append("department=?")
        values.append(user.department)

    if updates:
        values.append(user_id)
        cur.execute(f"UPDATE users SET {','.join(updates)} WHERE id=?", values)
        conn.commit()

    row = cur.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row)


@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor()

    if not cur.execute("SELECT 1 FROM users WHERE id=?", (user_id,)).fetchone():
        conn.close()
        raise HTTPException(404, "User not found")

    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    return {"message": f"User {user_id} deleted"}


# =========================
# INCIDENTS
# =========================

@app.get("/incidents")
def list_incidents():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM incidents").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/incidents/{incident_id}")
def get_incident(incident_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM incidents WHERE id=?", (incident_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Incident not found")
    return dict(row)


@app.post("/incidents")
def create_incident(incident: IncidentCreate):
    conn = get_connection()
    cur = conn.cursor()

    next_id = cur.execute("SELECT COALESCE(MAX(id),0)+1 FROM incidents").fetchone()[0]

    cur.execute(
        "INSERT INTO incidents VALUES (?, ?, ?, ?)",
        (next_id, incident.number, incident.description, incident.status)
    )

    conn.commit()
    conn.close()

    return {"id": next_id, **incident.dict()}


@app.put("/incidents/{incident_id}")
def update_incident(incident_id: int, incident: IncidentUpdate):
    conn = get_connection()
    cur = conn.cursor()

    if not cur.execute("SELECT 1 FROM incidents WHERE id=?", (incident_id,)).fetchone():
        conn.close()
        raise HTTPException(404, "Incident not found")

    updates, values = [], []

    if incident.number:
        updates.append("number=?")
        values.append(incident.number)
    if incident.description:
        updates.append("description=?")
        values.append(incident.description)
    if incident.status:
        updates.append("status=?")
        values.append(incident.status)

    if updates:
        values.append(incident_id)
        cur.execute(f"UPDATE incidents SET {','.join(updates)} WHERE id=?", values)
        conn.commit()

    row = cur.execute("SELECT * FROM incidents WHERE id=?", (incident_id,)).fetchone()
    conn.close()
    return dict(row)


@app.delete("/incidents/{incident_id}")
def delete_incident(incident_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM incidents WHERE id=?", (incident_id,))
    conn.commit()
    conn.close()

    return {"message": f"Incident {incident_id} deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
    