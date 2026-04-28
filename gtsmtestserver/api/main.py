from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import os

app = FastAPI(title="GTSM Test API", version="1.0.0")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "crud.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# --- Pydantic Models ---

class UserCreate(BaseModel):
    name: str
    email: str
    department: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None


class User(BaseModel):
    id: int
    name: str
    email: str
    department: str


class IncidentCreate(BaseModel):
    number: str
    description: str
    status: str = "open"


class IncidentUpdate(BaseModel):
    number: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class Incident(BaseModel):
    id: int
    number: str
    description: str
    status: str


# --- User Endpoints ---

@app.get("/users", response_model=List[User])
def list_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, department FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, department FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)


@app.post("/users", response_model=User)
def create_user(user: UserCreate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM users")
    next_id = (cursor.fetchone()[0] or 0) + 1
    cursor.execute(
        "INSERT INTO users (id, name, email, department) VALUES (?, ?, ?, ?)",
        (next_id, user.name, user.email, user.department)
    )
    conn.commit()
    cursor.execute("SELECT id, name, email, department FROM users WHERE id = ?", (next_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)


@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: UserUpdate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    updates = []
    values = []
    if user.name is not None:
        updates.append("name = ?")
        values.append(user.name)
    if user.email is not None:
        updates.append("email = ?")
        values.append(user.email)
    if user.department is not None:
        updates.append("department = ?")
        values.append(user.department)

    if updates:
        values.append(user_id)
        cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()

    cursor.execute("SELECT id, name, email, department FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)


@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"message": f"User {user_id} deleted"}


# --- Incident Endpoints ---

@app.get("/incidents", response_model=List[Incident])
def list_incidents():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, number, description, status FROM incidents")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/incidents/{incident_id}", response_model=Incident)
def get_incident(incident_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, number, description, status FROM incidents WHERE id = ?", (incident_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Incident not found")
    return dict(row)


@app.post("/incidents", response_model=Incident)
def create_incident(incident: IncidentCreate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM incidents")
    next_id = (cursor.fetchone()[0] or 0) + 1
    cursor.execute(
        "INSERT INTO incidents (id, number, description, status) VALUES (?, ?, ?, ?)",
        (next_id, incident.number, incident.description, incident.status)
    )
    conn.commit()
    cursor.execute("SELECT id, number, description, status FROM incidents WHERE id = ?", (next_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)


@app.put("/incidents/{incident_id}", response_model=Incident)
def update_incident(incident_id: int, incident: IncidentUpdate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM incidents WHERE id = ?", (incident_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Incident not found")

    updates = []
    values = []
    if incident.number is not None:
        updates.append("number = ?")
        values.append(incident.number)
    if incident.description is not None:
        updates.append("description = ?")
        values.append(incident.description)
    if incident.status is not None:
        updates.append("status = ?")
        values.append(incident.status)

    if updates:
        values.append(incident_id)
        cursor.execute(f"UPDATE incidents SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()

    cursor.execute("SELECT id, number, description, status FROM incidents WHERE id = ?", (incident_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)


@app.delete("/incidents/{incident_id}")
def delete_incident(incident_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM incidents WHERE id = ?", (incident_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Incident not found")
    cursor.execute("DELETE FROM incidents WHERE id = ?", (incident_id,))
    conn.commit()
    conn.close()
    return {"message": f"Incident {incident_id} deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
