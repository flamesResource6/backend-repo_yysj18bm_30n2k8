import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import db, create_document, get_documents
from bson import ObjectId

app = FastAPI(title="Lily — Your AI Recruiter (MVP)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- Helpers ---------
class RoleCreate(BaseModel):
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    level: Optional[str] = None
    description: str
    requirements: List[str] = []

class ApplicantCreate(BaseModel):
    name: str
    email: str
    role_id: Optional[str] = None
    resume_text: Optional[str] = None

class ChatTurn(BaseModel):
    interview_id: str
    message: str

class CodingRunRequest(BaseModel):
    interview_id: str
    language: str
    code: str
    input: Optional[str] = ""

# --------- Seed roles if empty ---------
@app.on_event("startup")
async def seed_roles():
    try:
        if db is None:
            return
        if "role" not in db.list_collection_names() or db["role"].count_documents({}) == 0:
            roles = [
                {
                    "title": "Frontend Engineer",
                    "department": "Engineering",
                    "location": "Remote",
                    "level": "Mid",
                    "description": "Build modern web UIs with React, TypeScript, and Tailwind.",
                    "requirements": ["React", "TypeScript", "CSS", "Testing"],
                },
                {
                    "title": "Backend Engineer",
                    "department": "Engineering",
                    "location": "Remote",
                    "level": "Senior",
                    "description": "Design APIs and services with Node/Go/Python.",
                    "requirements": ["API design", "Databases", "Cloud", "Testing"],
                },
                {
                    "title": "Data Analyst",
                    "department": "Data",
                    "location": "Hybrid",
                    "level": "Junior",
                    "description": "Analyze data and build dashboards.",
                    "requirements": ["SQL", "Python", "Visualization"],
                },
            ]
            for r in roles:
                create_document("role", r)
    except Exception:
        pass

# --------- Basic routes ---------
@app.get("/")
def read_root():
    return {"message": "Lily backend running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected"
            response["collections"] = db.list_collection_names()
    except Exception as e:
        response["database"] = f"⚠️ {str(e)[:60]}"
    return response

# --------- Roles ---------
@app.get("/api/roles")
def list_roles():
    items = get_documents("role") if db else []
    for it in items:
        it["id"] = str(it.pop("_id"))
    return {"roles": items}

@app.get("/api/roles/{role_id}")
def get_role(role_id: str):
    if db is None:
        return {"role": None}
    item = db["role"].find_one({"_id": ObjectId(role_id)})
    if not item:
        return {"role": None}
    item["id"] = str(item.pop("_id"))
    return {"role": item}

@app.post("/api/roles")
def create_role(role: RoleCreate):
    rid = create_document("role", role.model_dump())
    return {"id": rid}

# --------- Applicants / Application ---------
@app.post("/api/apply")
def apply(applicant: ApplicantCreate):
    aid = create_document("applicant", applicant.model_dump())
    return {"applicant_id": aid, "suggested_roles": ["Frontend Engineer", "Backend Engineer"]}

# File upload mock (resume)
@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    # Mock: read bytes and pretend to extract text
    content = await file.read()
    extracted_text = f"Extracted {len(content)} bytes of resume text. Skills: React, Python, SQL"
    return {"resume_text": extracted_text}

# --------- Interview flow (mock AI) ---------
@app.post("/api/interview/start")
def start_interview(applicant_id: str, role_id: str):
    iid = create_document("interview", {
        "applicant_id": applicant_id,
        "role_id": role_id,
        "mode": "chat",
        "messages": [
            {"sender": "lily", "text": "Hi! I’m Lily. Tell me about yourself."}
        ]
    })
    return {"interview_id": iid}

@app.post("/api/interview/chat")
def chat(turn: ChatTurn):
    # Mock conversation: echo + simple branching
    user_msg = turn.message.strip()
    reply = "Thanks! Can you share a challenging project you led?"
    if any(k in user_msg.lower() for k in ["react", "frontend", "ui"]):
        reply = "Great frontend background. How do you manage state at scale?"
    elif any(k in user_msg.lower() for k in ["python", "backend", "api"]):
        reply = "Nice backend focus. How do you design resilient APIs?"
    if db:
        db["interview"].update_one({"_id": ObjectId(turn.interview_id)}, {"$push": {"messages": {"sender": "candidate", "text": user_msg}}})
        db["interview"].update_one({"_id": ObjectId(turn.interview_id)}, {"$push": {"messages": {"sender": "lily", "text": reply}}})
    return {"reply": reply}

@app.post("/api/interview/coding/start")
def start_coding(interview_id: str):
    if db:
        db["interview"].update_one({"_id": ObjectId(interview_id)}, {"$set": {"mode": "coding"}})
    starter = "// Write a function to reverse a string\nfunction solve(s){\n  return s.split('').reverse().join('')\n}\nconsole.log(solve('hello'))\n"
    return {"starter_code": starter, "language": "javascript"}

@app.post("/api/interview/coding/run")
def run_code(req: CodingRunRequest):
    # Mock Judge0: We will not execute code. We just return mocked output based on keywords
    output = """Running tests...\nTest 1: PASSED\nTest 2: PASSED\nAll good!"""
    if "reverse" in req.code.lower():
        output = "All tests passed."
    elif "error" in req.code.lower():
        output = "Compilation error: Unexpected token"
    return {"stdout": output}

@app.post("/api/interview/complete")
def complete(interview_id: str):
    # Mock scoring
    result = {
        "communication": 82,
        "problem_solving": 76,
        "technical": 88,
        "summary": "Strong fundamentals, clear communication. Consider deeper system design practice."
    }
    rid = create_document("result", {"interview_id": interview_id, **result})
    return {"result_id": rid, **result}

# --------- Admin mocks ---------
@app.get("/api/admin/applicants")
def admin_applicants():
    if not db:
        return {"applicants": []}
    apps = list(db["applicant"].find().limit(50))
    for a in apps:
        a["id"] = str(a.pop("_id"))
    return {"applicants": apps}

@app.get("/api/admin/interviews")
def admin_interviews():
    if not db:
        return {"interviews": []}
    items = list(db["interview"].find().limit(50))
    for it in items:
        it["id"] = str(it.pop("_id"))
    return {"interviews": items}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
